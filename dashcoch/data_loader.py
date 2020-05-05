from datetime import date, datetime, timedelta
import confuse
import numpy as np
import pandas as pd
from pytz import timezone
from scipy import stats


class DataLoader:
    def __init__(self, cfg: confuse.Configuration):
        self.cfg = cfg

        #
        # Load info on the latest updates
        #
        if cfg["show"]["updates"]:
            self.last_updated = pd.read_csv(
                cfg["urls"]["last_updated"].get(), index_col=[0]
            ).sort_values(by=["Date", "Time"], ascending=False)

            self.last_updated = self.__get_iso(self.last_updated)

        # Load the data from the regions
        self.swiss_cases = pd.read_csv(cfg["urls"]["cases"].get())
        self.swiss_fatalities = pd.read_csv(cfg["urls"]["fatalities"].get())

        # Get Swiss demographical data
        self.regional_demography = pd.read_csv(
            cfg["urls"]["demography"].get(), index_col=0
        )

        self.swiss_cases_by_date = self.swiss_cases.set_index("Date")
        self.swiss_fatalities_by_date = self.swiss_fatalities.set_index("Date")

        self.swiss_cases_by_date_filled = self.swiss_cases_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_cases_by_date_diff = self.swiss_cases_by_date_filled.diff().replace(
            0, float("nan")
        )
        self.swiss_cases_by_date_diff["date_label"] = [
            date.fromisoformat(d).strftime("%d. %m.")
            for d in self.swiss_cases_by_date_diff.index.values
        ]

        self.swiss_fatalities_by_date_diff = self.swiss_fatalities_by_date.diff().replace(
            0, float("nan")
        )

        self.swiss_cases_by_date_filled = self.swiss_cases_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_fatalities_by_date_filled = self.swiss_fatalities_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_case_fatality_rates = (
            self.swiss_fatalities_by_date_filled / self.swiss_cases_by_date_filled
        )

        self.swiss_cases_by_date_filled_per_capita = (
            self.__get_swiss_cases_by_date_filled_per_capita()
        )

        self.latest_date = self.__get_latest_date()
        self.updated_regions = self.__get_updated_regions()
        self.new_swiss_cases = self.__get_new_cases()
        self.total_swiss_cases = self.__get_total_swiss_cases()
        self.total_swiss_fatalities = self.__get_total_swiss_fatalities()
        self.swiss_case_fatality_rate = (
            self.total_swiss_fatalities / self.total_swiss_cases
        )

        # Put the date at the end
        self.swiss_cases_as_dict = self.swiss_cases.to_dict("list")
        date_tmp = self.swiss_cases_as_dict.pop("Date")
        self.swiss_cases_as_dict["Date"] = date_tmp
        self.swiss_cases_normalized_as_dict = (
            self.__get_swiss_cases_as_normalized_dict()
        )

        self.swiss_fatalities_as_dict = self.swiss_fatalities.to_dict("list")
        self.region_labels = [
            region
            for region in self.swiss_cases_as_dict
            if region != self.cfg["settings"]["total_column_name"].get()
            and region != "Date"
        ]
        self.regional_centres = self.__get_regional_centres()

        #
        # Moving average showing development
        #
        self.moving_total = self.__get_moving_total(
            self.swiss_cases_by_date.diff()
        ).replace(0, float("nan"))

        #
        # Some regression analysis on the data
        #
        if cfg["show"]["demographic_correlation"]:
            self.prevalence_density_regression = self.__get_regression(
                self.regional_demography["Density"],
                self.swiss_cases_by_date_filled_per_capita.iloc[-1],
            )

            self.cfr_age_regression = self.__get_regression(
                self.regional_demography["O65"], self.swiss_case_fatality_rates.iloc[-1]
            )

        self.scaled_cases = self.__get_scaled_cases()

        #
        # Hospitalization Data
        #
        if cfg["show"]["hospitalizations"]:
            self.swiss_hospitalizations = pd.read_csv(
                cfg["urls"]["hospitalizations"].get()
            )
            self.swiss_icu = pd.read_csv(cfg["urls"]["icu"].get())
            self.swiss_vent = pd.read_csv(cfg["urls"]["vent"].get())
            self.swiss_hospitalizations_by_date = self.swiss_hospitalizations.set_index(
                "Date"
            )

            self.swiss_hospitalizations_by_date_diff = self.swiss_hospitalizations_by_date.diff().replace(
                0, float("nan")
            )

            self.swiss_hospitalizations_by_date_filled = self.swiss_hospitalizations_by_date.fillna(
                method="ffill", axis=0
            )

        if cfg["show"]["hospital_releases"]:
            self.swiss_releases = pd.read_csv(cfg["urls"]["releases"].get())

        #
        # Get age distribution data
        #
        if cfg["show"]["age_distribution"]:
            self.age_data = pd.read_csv(cfg["urls"]["age_distribution"].get())
            self.age_data["region"] = self.age_data[
                self.cfg["settings"]["age_distribution_region_column_name"].get()
            ]

            self.age_data_male_hist = self.age_data[
                self.age_data["sex"] == "Male"
            ].replace(0, np.nan)
            self.age_data_female_hist = self.age_data[
                self.age_data["sex"] == "Female"
            ].replace(0, np.nan)

        #
        # Get testing data
        #
        if cfg["show"]["tests"]:
            self.tests = pd.read_csv(cfg["urls"]["tests"].get(), index_col=[0])
            self.tests["pos_rate"] = np.round(self.tests["pos_rate"] * 100, 2)

        #
        # World related data
        #
        if cfg["show"]["international"]:
            self.world_cases = self.__simplify_world_data(
                pd.read_csv(cfg["urls"]["world_cases"].get())
            )

            self.world_fataltities = self.__simplify_world_data(
                pd.read_csv(cfg["urls"]["world_fatalities"].get())
            )

            self.world_population = self.cfg["countries"].get()

            self.world_case_fatality_rate = (
                self.world_fataltities.iloc[-1] / self.world_cases.iloc[-1]
            )

            self.swiss_world_cases_normalized = (
                self.__get_swiss_world_cases_normalized()
            )

    def __get_iso(self, df):
        isos = []
        updated_today = []
        for _, row in df.iterrows():
            t = row["Time"]

            if len(t) == 4:
                t = "0" + t
            if len(t) == 5:
                t += ":00"

            iso = datetime.fromisoformat(row["Date"] + "T" + t)
            isos.append(iso)
            updated_today.append(iso.date() == datetime.today().date())

        df["ISO"] = isos
        df["Updated_Today"] = updated_today

        return df

    def __get_latest_date(self):
        return self.swiss_cases.iloc[len(self.swiss_cases) - 1]["Date"]

    def __get_updated_regions(self):
        l = len(self.swiss_cases_by_date)
        return [
            region
            for region in self.swiss_cases_by_date.iloc[l - 1][
                self.swiss_cases_by_date.iloc[l - 1].notnull()
            ].index
        ]

    def __get_swiss_cases_by_date_filled_per_capita(self):
        tmp = self.swiss_cases_by_date_filled.copy()
        for column in tmp:
            tmp[column] = (
                tmp[column] / self.regional_demography["Population"][column] * 10000
            )
        return tmp

    def __get_new_cases(self):
        if (
            date.fromisoformat(self.latest_date)
            != datetime.now(timezone("Europe/Zurich")).date()
        ):
            return 0

        l = len(self.swiss_cases_by_date_filled)
        return (
            self.swiss_cases_by_date_filled.diff().iloc[l - 1].sum()
            - self.swiss_cases_by_date_filled.diff().iloc[l - 1][
                self.cfg["settings"]["total_column_name"].get()
            ]
        )

    def __get_total_swiss_cases(self):
        l = len(self.swiss_cases_by_date_filled)
        return (
            self.swiss_cases_by_date_filled.iloc[l - 1].sum()
            - self.swiss_cases_by_date_filled.iloc[l - 1][
                self.cfg["settings"]["total_column_name"].get()
            ]
        )

    def __get_total_swiss_fatalities(self):
        return self.swiss_fatalities_by_date_filled.iloc[-1][
            self.cfg["settings"]["total_column_name"].get()
        ]

    def __get_swiss_cases_as_normalized_dict(self):
        tmp = [
            (
                str(region),
                [
                    round(i, 2)
                    for i in self.swiss_cases_as_dict[region]
                    / self.regional_demography["Population"][region]
                    * 10000
                ],
            )
            for region in self.swiss_cases_as_dict
            if region != "Date"
        ]
        tmp.append(("Date", self.swiss_cases_as_dict["Date"]))
        return dict(tmp)

    def __simplify_world_data(self, df: pd.DataFrame):
        df.drop(columns=["Lat", "Long"], inplace=True)
        df["Province/State"].fillna("", inplace=True)
        df = df.rename(columns={"Country/Region": "Day"})
        df = df.groupby("Day").sum()
        df = df.T
        df.drop(
            df.columns.difference(
                [c for c in [*self.cfg["countries"].get()] if c != "Switzerland"]
            ),
            1,
            inplace=True,
        )
        df.index = range(0, len(df))
        return df

    def __get_swiss_world_cases_normalized(self, min_prevalence: int = 0.4):
        tmp = self.world_cases.copy()
        # Don't take today from switzerland, as values are usually very incomplete
        tmp["Switzerland"] = pd.Series(
            self.swiss_cases_as_dict[self.cfg["settings"]["total_column_name"].get()][
                :-1
            ]
        )

        for column in tmp:
            tmp[column] = tmp[column] / self.world_population[column] * 10000

        tmp[tmp < min_prevalence] = 0
        for column in tmp:
            while tmp[column].iloc[0] == 0:
                tmp[column] = tmp[column].shift(-1)
        tmp.dropna(how="all", inplace=True)

        return tmp

    def __get_regression(self, x, y):
        df = pd.DataFrame([x, y])
        df = df.dropna(axis=1, how="any")
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df.iloc[0], df.iloc[1]
        )
        m = df.iloc[0].min() + (df.iloc[0].max() - df.iloc[0].min()) / 2
        return {
            "slope": slope,
            "intercept": intercept,
            "r_value": r_value,
            "p_value": p_value,
            "std_err": std_err,
            "x": [df.iloc[0].min(), m, df.iloc[0].max()],
            "y": [
                slope * df.iloc[0].min() + intercept,
                slope * m + intercept,
                slope * df.iloc[0].max() + intercept,
            ],
        }

    def __get_scaled_cases(self):
        cases = self.swiss_cases_by_date_filled.iloc[-1][0:-1]
        min_cases = cases.min()
        max_cases = cases.max()
        scaled_cases = (cases - min_cases) / (max_cases - min_cases) * (20) + 10
        return scaled_cases

    def __get_moving_total(self, df, days=7):
        offset = days - 1
        df_moving_total = df[0:0]
        for i in range(0, len(df)):
            start = max(0, i - offset)
            d = pd.Series(df.iloc[start : i + 1].sum().to_dict())
            d.name = df.index[i]
            df_moving_total = df_moving_total.append(d)

        # Add the label for the date range (previous week)
        date_labels = []
        for d in df_moving_total.index.values:
            today = date.fromisoformat(d)
            date_labels.append(
                (today - timedelta(days=7)).strftime("%d. %m.")
                + " – "
                + today.strftime("%d. %m.")
            )

        df_moving_total["date_label"] = date_labels

        return df_moving_total

    def __get_regional_centres(self):
        regions = self.cfg["regions"].get()
        return {d["region"]: {"lat": d["lat"], "lon": d["lon"]} for d in regions}
