import math
from datetime import date, datetime, timedelta
import confuse
import numpy as np
import pandas as pd
from pytz import timezone
from scipy import stats

COLS = [
    "ZH",
    "BE",
    "LU",
    "UR",
    "SZ",
    "OW",
    "NW",
    "GL",
    "ZG",
    "FR",
    "SO",
    "BS",
    "BL",
    "SH",
    "AR",
    "AI",
    "SG",
    "GR",
    "AG",
    "TG",
    "TI",
    "VD",
    "VS",
    "NE",
    "GE",
    "JU",
    "CH",
    "Date",
]


class DataLoader:
    def __init__(self, cfg: confuse.Configuration):
        self.cfg = cfg

        self.total_column_name = cfg["settings"]["total_column_name"].get()

        #
        # Load info on the latest updates
        #
        if cfg["show"]["updates"]:
            self.last_updated = pd.read_csv(
                cfg["urls"]["last_updated"].get(), index_col=[0]
            ).sort_values(by=["Date", "Time"], ascending=False)

            self.last_updated["Date"] = pd.to_datetime(self.last_updated["Date"])
            self.last_updated = self.__get_iso(self.last_updated)

        # Load the data from the regions
        self.swiss_cases = pd.read_csv(cfg["urls"]["cases"].get(), usecols=COLS)
        self.swiss_fatalities = pd.read_csv(
            cfg["urls"]["fatalities"].get(), usecols=COLS
        )

        self.swiss_cases["Date"] = pd.to_datetime(self.swiss_cases["Date"])
        self.swiss_fatalities["Date"] = pd.to_datetime(self.swiss_fatalities["Date"])

        # Get Swiss demographical data
        self.regional_demography = pd.read_csv(
            cfg["urls"]["demography"].get(), index_col=0
        )

        self.swiss_cases_by_date = self.swiss_cases.set_index("Date")
        self.swiss_fatalities_by_date = self.swiss_fatalities.set_index("Date")
        self.swiss_cases_updated_mask_by_date = ~self.swiss_cases_by_date.isnull()

        self.swiss_cases_by_date_filled = self.swiss_cases_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_cases_by_date_diff = self.swiss_cases_by_date_filled.diff().replace()

        self.swiss_cases_by_date_diff[self.total_column_name + "_rolling"] = np.round(
            self.swiss_cases_by_date_diff[self.total_column_name]
            .rolling(7, center=True, min_periods=1)
            .mean(),
            0,
        )

        self.swiss_cases_by_date_diff.loc[
            self.swiss_cases_by_date_diff.tail(7).index,
            self.total_column_name + "_rolling",
        ] = np.nan

        self.swiss_cases_by_date_diff["date_label"] = [
            pd.to_datetime(str(d)).strftime("%d. %m.")
            for d in self.swiss_cases_by_date_diff.index.values
        ]

        self.swiss_cases_by_date_diff["weekday_number"] = [
            pd.to_datetime(str(d)).weekday()
            for d in self.swiss_cases_by_date_diff.index.values
        ]

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        self.swiss_cases_by_date_diff["weekday"] = [
            weekdays[w] for w in self.swiss_cases_by_date_diff["weekday_number"]
        ]

        week = 0
        weeks = []
        for d in self.swiss_cases_by_date_diff["weekday_number"].values:
            weeks.append(week)

            if d == 6:
                week += 1

        self.swiss_cases_by_date_diff["week"] = weeks

        self.swiss_fatalities_by_date_diff = (
            self.swiss_fatalities_by_date.diff().replace()
        )

        self.swiss_fatalities_by_date_diff[
            self.total_column_name + "_rolling"
        ] = np.round(
            self.swiss_fatalities_by_date_diff[self.total_column_name]
            .rolling(7, center=True, min_periods=1)
            .mean(),
            0,
        )

        self.swiss_fatalities_by_date_diff.loc[
            self.swiss_fatalities_by_date_diff.tail(7).index,
            self.total_column_name + "_rolling",
        ] = np.nan

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
        self.new_swiss_cases = max(0, self.__get_new_cases())
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
            if region != self.total_column_name and region != "Date"
        ]
        self.regional_centres = self.__get_regional_centres()

        #
        # Moving average showing development
        #
        self.moving_total = self.__get_moving_total(
            self.swiss_cases_by_date.diff()
        ).replace(0, float("nan"))

        #
        # Hospitalization Data
        #
        if cfg["show"]["hospitalizations"]:
            self.swiss_hospitalizations = pd.read_csv(
                cfg["urls"]["hospitalizations"].get(), usecols=COLS
            )
            self.swiss_icu = pd.read_csv(cfg["urls"]["icu"].get(), usecols=COLS)
            self.swiss_vent = pd.read_csv(cfg["urls"]["vent"].get(), usecols=COLS)
            self.swiss_hospitalizations_by_date = self.swiss_hospitalizations.set_index(
                "Date"
            )

            self.swiss_hospitalizations_by_date_diff = (
                self.swiss_hospitalizations_by_date.diff().replace(0, float("nan"))
            )

            self.swiss_hospitalizations_by_date_filled = (
                self.swiss_hospitalizations_by_date.fillna(method="ffill", axis=0)
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
            self.tests = self.tests[
                self.tests.index >= cfg["settings"]["start_date"].get()
            ]
            self.tests["pos_rate"] = np.round(self.tests["pos_rate"] * 100, 2)

            self.tests["pos_rate_rolling"] = (
                self.tests["pos_rate"].rolling(7, center=True).mean()
            )

        #
        # World related data
        #
        if cfg["show"]["international"]:
            # self.world_cases = self.__simplify_world_data(
            #     pd.read_csv(cfg["urls"]["world_cases"].get())
            # )

            self.world = pd.read_csv(cfg["urls"]["world"].get())
            self.world = self.world[
                (self.world["location"].isin([*self.cfg["countries"].get()]))
                & (self.world["date"] >= "2020-05-31")
            ]

            # Set new for last of May to zero, so all start at 0
            self.world.loc[
                self.world["date"] == "2020-05-31",
                ["new_cases", "new_deaths", "new_tests"],
            ] = 0

            self.world["total_cases"] = (
                self.world.groupby("location")["new_cases"].cumsum().fillna(0)
            )
            self.world["total_deaths"] = (
                self.world.groupby("location")["new_deaths"].cumsum().fillna(0)
            )
            self.world["total_tests"] = (
                self.world.groupby("location")["new_tests"].cumsum().fillna(0)
            )
            self.world["total_cases_per_ten_thousand"] = (
                self.world["total_cases"] / self.world["population"] * 10000
            ).round(decimals=3)
            self.world["total_deaths_per_ten_thousand"] = (
                self.world["total_deaths"] / self.world["population"] * 10000
            ).round(decimals=3)
            self.world["cfr"] = (
                self.world["total_deaths"] / self.world["total_cases"]
            ).round(decimals=3)
            self.world["new_tests_smoothed_per_ten_thousand"] = (
                self.world["new_tests_smoothed"] / self.world["population"] * 10000
            ).round(decimals=3)
            self.world["date_label"] = pd.to_datetime(self.world["date"]).dt.strftime(
                "%d. %m."
            )
            # Put in per-country dict to avoid doing this with every callback
            tmp = {}
            self.world_no_na = {}
            for country in self.world["location"].unique():
                tmp[country] = self.world[self.world["location"] == country].copy()
                self.world_no_na[country] = (
                    self.world[self.world["location"] == country]
                    .copy()
                    .dropna(
                        subset=["new_tests_smoothed_per_ten_thousand", "positive_rate"]
                    )
                )
            self.world = tmp

    def __get_iso(self, df):
        isos = []
        updated_today = []
        for _, row in df.iterrows():
            t = row["Time"]

            if len(t) == 4:
                t = "0" + t
            if len(t) == 5:
                t += ":00"

            iso = datetime.fromisoformat(str(row["Date"].date()) + "T" + t)
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
        if self.latest_date.date() != datetime.now(timezone("Europe/Zurich")).date():
            return 0

        l = len(self.swiss_cases_by_date_filled)
        return (
            self.swiss_cases_by_date_filled.diff().iloc[l - 1].sum()
            - self.swiss_cases_by_date_filled.diff().iloc[l - 1][self.total_column_name]
        )

    def __get_total_swiss_cases(self):
        l = len(self.swiss_cases_by_date_filled)
        return (
            self.swiss_cases_by_date_filled.iloc[l - 1].sum()
            - self.swiss_cases_by_date_filled.iloc[l - 1][self.total_column_name]
        )

    def __get_total_swiss_fatalities(self):
        return self.swiss_fatalities_by_date_filled.iloc[-1][self.total_column_name]

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
            df.columns.difference([c for c in [*self.cfg["countries"].get()]]),
            1,
            inplace=True,
        )
        df.index = range(0, len(df))
        return df

    def __get_swiss_world_cases_normalized(self, min_prevalence: int = 0.4):
        tmp = self.world_cases.copy()

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
            today = pd.to_datetime(str(d))
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
