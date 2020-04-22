import time
from dashcoch import DataLoader, StyleLoader
import math
from datetime import date, datetime, timedelta
from pytz import timezone
import confuse
import geojson
import flask
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ClientsideFunction
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dashcoch.config import config as cfg

external_scripts = [
    "https://cdn.simpleanalytics.io/hello.js",
]

lang = 0

# external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

meta_tags = [
    # {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    {"property": "og:title", "content": cfg["i18n"]["title"][lang].get()},
    {"property": "og:type", "content": "website"},
    {
        "property": "og:description",
        "content": "Latest updates of COVID-19 development in Switzerland",
    },
    {"property": "og:url", "content": cfg["i18n"]["description"][lang].get()},
    {
        "property": "og:image",
        "content": "https://www.corona-data.ch/assets/embed-social-414x414.jpg",
    },
]

app = dash.Dash(
    __name__,
    external_scripts=external_scripts,
    # external_stylesheets=external_stylesheets,
    meta_tags=meta_tags,
)
server = app.server

app.title = cfg["i18n"]["title"][lang].get()
style = StyleLoader(cfg)


def get_data():
    global data
    data = DataLoader(cfg)


def update_data(period=int(cfg["settings"]["update_interval"].get())):
    while True:
        get_data()
        print("Data updated at " + datetime.now().isoformat())
        time.sleep(period)


get_data()


def get_lang():
    supported_languages = cfg["settings"]["languages"].get()

    if "Referer" in flask.request.headers:
        url_lang = flask.request.headers["Referer"].split("/")[-1]
        if url_lang in supported_languages:
            return supported_languages.index(url_lang)

    candidate = flask.request.accept_languages.best_match(supported_languages)
    if candidate in supported_languages:
        return supported_languages.index(candidate)
    else:
        return cfg["settings"]["default_language"].get()


def get_layout():
    global lang

    try:
        if flask.has_request_context():
            lang = get_lang()
    except:
        lang = cfg["settings"]["default_language"].get()

    content = [dcc.Location(id="url", refresh=False)]

    # Header
    if cfg["show"]["header"]:
        content.extend(
            [
                html.Div(
                    id="header",
                    children=[
                        html.P(
                            id="language-picker",
                            children=[
                                dcc.Link(
                                    children=html.Span(children=l),
                                    refresh=True,
                                    href="/" + l,
                                )
                                for l in cfg["settings"]["languages"].get()
                            ],
                        ),
                        html.Img(
                            src=cfg["logo"]["src"].get(),
                            style={
                                "width": cfg["logo"]["width"].get(),
                                "display": cfg["logo"]["display"].get(),
                            },
                        ),
                        html.H3(children=cfg["i18n"]["title"][lang].get()),
                        html.P(
                            children=(
                                [dcc.Markdown(cfg["i18n"]["info"][lang].get())]
                                if cfg["show"]["info"].get()
                                else []
                            )
                        ),
                        html.P(
                            id="sci-info",
                            children=(
                                [dcc.Markdown(cfg["i18n"]["more_info"][lang].get())]
                                if cfg["show"]["more_info"].get()
                                else []
                            ),
                        ),
                        html.Br(),
                        html.P(
                            id="glueckskette",
                            style={"display": cfg["banner"]["display"].get()},
                            children=[
                                html.A(
                                    [
                                        html.Img(
                                            style={
                                                "maxWidth": "100%",
                                                "width": cfg["banner"]["width"].get(),
                                            },
                                            src=cfg["banner"]["src"].get(),
                                        ),
                                    ],
                                    href=cfg["banner"]["href"].get(),
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )

    # Totals
    if cfg["show"]["totals"]:
        content.extend(
            [
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[
                                html.Div(
                                    className="total-container",
                                    children=[
                                        html.P(
                                            className="total-title",
                                            children=cfg["i18n"][
                                                "total_reported_cases"
                                            ][lang].get(),
                                        ),
                                        html.Div(
                                            className="total-content",
                                            children=str(int(data.total_swiss_cases)),
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="total-container",
                                    children=[
                                        html.P(
                                            className="total-title",
                                            children=cfg["i18n"][
                                                "reported_cases_today"
                                            ][lang].get(),
                                        ),
                                        html.Div(
                                            className="total-content",
                                            children="+"
                                            + str(int(data.new_swiss_cases)),
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="total-container",
                                    children=[
                                        html.P(
                                            className="total-title",
                                            children=cfg["i18n"]["total_fatalities"][
                                                lang
                                            ].get(),
                                        ),
                                        html.Div(
                                            className="total-content",
                                            children=str(
                                                int(data.total_swiss_fatalities)
                                            ),
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="total-container",
                                    children=[
                                        html.P(
                                            className="total-title",
                                            children=cfg["i18n"][
                                                "regions_updated_today"
                                            ][lang].get(),
                                        ),
                                        html.Div(
                                            className="total-content",
                                            children=str(
                                                data.last_updated["Updated_Today"].sum()
                                            )
                                            + " / "
                                            + str(len(data.last_updated)),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(className="six columns"),
                        html.Div(className="six columns"),
                    ],
                ),
            ]
        )

    # Updated regions
    if cfg["show"]["updates"]:
        content.extend(
            [
                html.Div(
                    id="update-container",
                    className="slider-container",
                    children=[
                        html.Div(children=cfg["i18n"]["latest_updates"][lang].get())
                    ]
                    + [
                        html.Span(
                            className=str(vals["Updated_Today"]),
                            children=region
                            + ": "
                            + date.fromisoformat(vals["Date"]).strftime("%d. %m.")
                            + " "
                            + vals["Time"],
                        )
                        for region, vals in data.last_updated.iterrows()
                    ],
                ),
            ]
        )

    # Map
    if cfg["show"]["map"]:
        content.extend(
            [
                html.Div(
                    className="slider-container",
                    children=[
                        dcc.RadioItems(
                            id="radio-prevalence",
                            options=[
                                {
                                    "label": cfg["i18n"]["total_reported_cases"][
                                        lang
                                    ].get(),
                                    "value": "number",
                                },
                                {
                                    "label": cfg["i18n"]["new_cases"][lang].get(),
                                    "value": "new",
                                },
                                {
                                    "label": cfg["i18n"]["cumulative_prevalence"][
                                        lang
                                    ].get(),
                                    "value": "prevalence",
                                },
                                {
                                    "label": cfg["i18n"]["new_hospitalizations"][
                                        lang
                                    ].get(),
                                    "value": "new_hospitalizations",
                                },
                                {
                                    "label": cfg["i18n"]["total_hospitalizations"][
                                        lang
                                    ].get(),
                                    "value": "hospitalizations",
                                },
                                {
                                    "label": cfg["i18n"]["new_fatalities"][lang].get(),
                                    "value": "new_fatalities",
                                },
                                {
                                    "label": cfg["i18n"]["total_fatalities"][
                                        lang
                                    ].get(),
                                    "value": "fatalities",
                                },
                            ],
                            value="number",
                            labelStyle={
                                "display": "inline-block",
                                "color": style.theme["foreground"],
                            },
                        ),
                    ],
                ),
                html.Div(id="date-container", className="slider-container"),
                html.Div(
                    children=[dcc.Graph(id="graph-map", config={"staticPlot": True},),]
                ),
                html.Div(
                    className="slider-container",
                    children=[
                        html.P(
                            className="slider-text",
                            children=cfg["i18n"]["drag_the_slider_to_change_the_date"][
                                lang
                            ].get(),
                        ),
                        dcc.Slider(
                            id="slider-date",
                            min=0,
                            max=len(data.swiss_cases["Date"]) - 1,
                            marks={
                                i: date.fromisoformat(d).strftime("%d. %m.")
                                for i, d in enumerate(data.swiss_cases["Date"])
                                if date.fromisoformat(d).weekday() == 0
                            },
                            value=len(data.swiss_cases["Date"]) - 1,
                            updatemode="drag",
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Main Data
    if cfg["show"]["main"]:
        content.extend(
            [
                html.H4(
                    children=cfg["i18n"]["main_data_title"][lang].get(),
                    style={"color": style.theme["accent"]},
                ),
                html.Div(
                    className="info-container",
                    children=[html.P(children=cfg["i18n"]["info_main"][lang].get())],
                ),
                html.Div(
                    className="slider-container",
                    children=[
                        dcc.RadioItems(
                            id="radio-scale-switzerland",
                            options=[
                                {
                                    "label": cfg["i18n"]["linear_scale"][lang].get(),
                                    "value": "linear",
                                },
                                {
                                    "label": cfg["i18n"]["log_scale"][lang].get(),
                                    "value": "log",
                                },
                            ],
                            value="linear",
                            labelStyle={
                                "display": "inline-block",
                                "color": style.theme["foreground"],
                            },
                        ),
                    ],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="case-ch-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="fatalities-ch-graph")],
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="new-case-ch-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="new-fatalities-ch-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Hospitalization Data
    if cfg["show"]["hospitalizations"] and cfg["show"]["hospital_releases"]:
        content.extend(
            [
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="hospitalizations-ch-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="releases-ch-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    if cfg["show"]["hospitalizations"] and not cfg["show"]["hospital_releases"]:
        content.extend(
            [
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="hospitalizations-ch-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Log-Log Development Plot
    if cfg["show"]["log_log_development"]:
        content.extend(
            [
                html.Div(
                    className="info-container",
                    children=[
                        html.P(children=cfg["i18n"]["info_log_log_main"][lang].get())
                    ],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="caseincrease-ch-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # International Data
    if cfg["show"]["international"]:
        content.extend(
            [
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="case-world-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="fatalities-world-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Age Distribution
    if cfg["show"]["age_distribution"]:
        content.extend(
            [
                html.H4(
                    children=cfg["i18n"]["age_distribution_title"][lang].get(),
                    className="secondary",
                    style={"color": style.theme["accent_secondary"]},
                ),
                html.Div(
                    className="info-container",
                    children=[
                        html.P(
                            children=cfg["i18n"]["info_age_distribution"][lang].get()
                        )
                    ],
                ),
                html.Div(
                    className="slider-container-secondary",
                    children=[
                        html.P(
                            className="slider-text",
                            children=cfg["i18n"]["show_data_for"][lang].get(),
                        ),
                        dcc.Dropdown(
                            id="select-regions-ch",
                            options=[
                                {"label": region, "value": region}
                                for region in [
                                    cfg["settings"]["total_column_name"].get()
                                ]
                                + data.region_labels
                            ],
                            value=cfg["settings"]["total_column_name"].get(),
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="slider-container-secondary",
                    children=[
                        dcc.RadioItems(
                            id="radio-absolute-norm",
                            options=[
                                {
                                    "label": cfg["i18n"]["absolute_numbers"][
                                        lang
                                    ].get(),
                                    "value": "absolute",
                                },
                                {
                                    "label": cfg["i18n"]["scaled_by_age_dist"][
                                        lang
                                    ].get(),
                                    "value": "scaled",
                                },
                            ],
                            value="absolute",
                            labelStyle={
                                "display": "inline-block",
                                "color": style.theme["foreground_secondary"],
                            },
                        ),
                    ],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="cases-bag-graph")],
                        ),
                    ],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="fatalities-bag-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Region Data
    if cfg["show"]["regional"]:
        content.extend(
            [
                html.H4(
                    children=cfg["i18n"]["regional_data_title"][lang].get(),
                    style={"color": style.theme["accent"]},
                ),
                html.Div(
                    className="info-container",
                    children=[
                        html.P(children=cfg["i18n"]["info_regional"][lang].get())
                    ],
                ),
                html.Div(
                    id="plot-settings-container",
                    children=[
                        dcc.RadioItems(
                            id="radio-scale-regions",
                            options=[
                                {
                                    "label": cfg["i18n"]["linear_scale"][lang].get(),
                                    "value": "linear",
                                },
                                {
                                    "label": cfg["i18n"]["log_scale"][lang].get(),
                                    "value": "log",
                                },
                            ],
                            value="linear",
                            labelStyle={
                                "display": "inline-block",
                                "color": style.theme["foreground"],
                            },
                        ),
                        html.Br(),
                        dcc.Dropdown(
                            id="dropdown-regions",
                            options=[
                                {"label": region, "value": region}
                                for region in data.region_labels
                            ],
                            value=data.region_labels,
                            multi=True,
                        ),
                    ],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="case-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="case-pc-graph"),],
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="case-graph-diff")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Regional Log-Log Development Plot
    if cfg["show"]["log_log_regional_development"]:
        content.extend(
            [
                html.Div(
                    className="info-container",
                    children=[
                        html.P(
                            children=cfg["i18n"]["info_log_log_regional"][lang].get()
                        )
                    ],
                ),
                html.Div(id="date-container-regional", className="slider-container"),
                html.Div(id="caseincrease-regional-data", style={"display": "none"}),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="twelve columns",
                            children=[dcc.Graph(id="caseincrease-regional-graph")],
                        ),
                    ],
                ),
                html.Div(
                    className="slider-container",
                    children=[
                        html.P(
                            className="slider-text",
                            children=cfg["i18n"]["drag_the_slider_to_change_the_date"][
                                lang
                            ].get(),
                        ),
                        dcc.Slider(
                            id="slider-date-regional",
                            min=0,
                            max=len(data.swiss_cases["Date"]) - 1,
                            step=1,
                            value=len(data.moving_total) - 1,
                            updatemode="drag",
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Demographic Correlation
    if cfg["show"]["demographic_correlation"]:
        content.extend(
            [
                html.H4(
                    children=cfg["i18n"]["demographic_correlation_title"][lang].get(),
                    style={"color": style.theme["accent"]},
                ),
                html.Div(
                    className="info-container",
                    children=[html.P(children=cfg["i18n"]["info_corr"][lang].get())],
                ),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="prevalence-density-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="cfr-age-graph")],
                        ),
                    ],
                ),
                html.Br(),
            ]
        )

    # Raw Data
    if cfg["show"]["raw"]:
        content.extend(
            [
                html.H4(
                    children=cfg["i18n"]["raw_data_title"][lang].get(),
                    style={"color": style.theme["accent"]},
                ),
                html.P(
                    id="source-paragraph",
                    children=[
                        dcc.Markdown(cfg["i18n"]["raw_data_content"][lang].get())
                    ],
                ),
            ]
        )

    return html.Div(id="main", children=content)


app.layout = get_layout

# -------------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------------
try:

    @app.callback(
        dash.dependencies.Output("date-container", "children"),
        [dash.dependencies.Input("slider-date", "value")],
    )
    def update_map_date(selected_date_index):

        d = date.fromisoformat(data.swiss_cases["Date"].iloc[selected_date_index])
        return d.strftime("%d. %m. %Y")


except:
    pass

#
# The Map
#
try:

    @app.callback(
        Output("graph-map", "figure"),
        [Input("slider-date", "value"), Input("radio-prevalence", "value")],
    )
    def update_graph_map(selected_date_index, mode):
        d = data.swiss_cases["Date"].iloc[selected_date_index]

        map_data = data.swiss_cases_by_date_filled
        labels = [
            region + ": " + str(int(map_data[region][d]))
            if not math.isnan(float(map_data[region][d]))
            else ""
            for region in data.regional_centres
        ]

        if mode == "prevalence":
            map_data = data.swiss_cases_by_date_filled_per_capita
            labels = [
                region + ": " + str(round((map_data[region][d]), 1))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]
        elif mode == "fatalities":
            map_data = data.swiss_fatalities_by_date_filled
            labels = [
                region + ": " + str(int(map_data[region][d]))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]
        elif mode == "new":
            map_data = data.swiss_cases_by_date_diff
            labels = [
                region + ": " + str(int(map_data[region][d]))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]
        elif mode == "new_fatalities":
            map_data = data.swiss_fatalities_by_date_diff
            labels = [
                region + ": " + str(int(map_data[region][d]))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]
        elif mode == "new_hospitalizations":
            map_data = data.swiss_hospitalizations_by_date_diff
            labels = [
                region + ": " + str(int(map_data[region][d]))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]
        elif mode == "hospitalizations":
            map_data = data.swiss_hospitalizations_by_date_filled
            labels = [
                region + ": " + str(int(map_data[region][d]))
                if not math.isnan(float(map_data[region][d]))
                else ""
                for region in data.regional_centres
            ]

        return {
            "data": [
                {
                    "lat": [
                        data.regional_centres[region]["lat"]
                        for region in data.regional_centres
                    ],
                    "lon": [
                        data.regional_centres[region]["lon"]
                        for region in data.regional_centres
                    ],
                    "text": labels,
                    "mode": "text",
                    "type": "scattergeo",
                    "textfont": {
                        "family": "Arial, sans-serif",
                        "size": 16,
                        "color": "white",
                        "weight": "bold",
                    },
                },
                {
                    "type": "choropleth",
                    "showscale": False,
                    "locations": data.region_labels,
                    "z": [
                        map_data[region][d]
                        for region in map_data
                        if region != cfg["settings"]["total_column_name"].get()
                    ],
                    "colorscale": style.turbo,
                    "geojson": cfg["settings"]["choropleth"]["geojson_file"].get(),
                    "featureidkey": cfg["settings"]["choropleth"]["feature"].get(),
                    "marker": {"line": {"width": 0.0, "color": "#08302A"}},
                    # "colorbar": {
                    #     "thickness": 10,
                    #     "bgcolor": "#252e3f",
                    #     "tickfont": {"color": "white"},
                    # },
                },
            ],
            "layout": {
                "geo": {
                    "visible": False,
                    "center": cfg["settings"]["choropleth"]["center"].get(),
                    "lataxis": {
                        "range": cfg["settings"]["choropleth"]["lataxis"].get()
                    },
                    "lonaxis": {
                        "range": cfg["settings"]["choropleth"]["lonaxis"].get()
                    },
                    "projection": {"type": "transverse mercator"},
                },
                "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                "height": 600,
                "plot_bgcolor": "#252e3f",
                "paper_bgcolor": "#252e3f",
            },
        }


except:
    pass

#
# Total cases Switzerland
#
try:

    @app.callback(
        Output("case-ch-graph", "figure"), [Input("radio-scale-switzerland", "value")],
    )
    def update_case_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_cases.iloc[:-3]["Date"],
                    "y": data.swiss_cases.iloc[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_cases.iloc[-4:]["Date"],
                    "y": data.swiss_cases.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(44, 254, 193, 0.25)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_total_reported_cases_country_title"][
                    lang
                ].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_total_reported_cases_country_x"][
                        lang
                    ].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_total_reported_cases_country_y"][
                        lang
                    ].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    }
                ],
                "annotations": [
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    }
                ],
            },
        }


except:
    pass

#
# Total fatalities Switzerland
#
try:

    @app.callback(
        Output("fatalities-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_fatalities_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_fatalities[:-3]["Date"],
                    "y": data.swiss_fatalities[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_fatalities.iloc[-4:]["Date"],
                    "y": data.swiss_fatalities.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(44, 254, 193, 0.25)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_total_fatalities_country_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_total_fatalities_country_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_total_fatalities_country_y"][lang].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    }
                ],
                "annotations": [
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    }
                ],
            },
        }


except:
    pass

#
# New cases Switzerland
#
try:

    @app.callback(
        Output("new-case-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_new_case_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_cases_by_date_diff.iloc[:-3].index,
                    "y": data.swiss_cases_by_date_diff.iloc[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_cases_by_date_diff.iloc[-4:].index,
                    "y": data.swiss_cases_by_date_diff.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(44, 254, 193, 0.25)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_daily_reported_cases_country_title"][
                    lang
                ].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_daily_reported_cases_country_x"][
                        lang
                    ].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_daily_reported_cases_country_y"][
                        lang
                    ].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "line",
                        "xref": "x",
                        "yref": "paper",
                        "x0": "2020-03-16",
                        "y0": 0,
                        "x1": "2020-03-16",
                        "y1": 1,
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
                    },
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    },
                ],
                "annotations": [
                    {
                        "x": "2020-03-16",
                        "y": 0.92,
                        "xref": "x",
                        "yref": "paper",
                        "text": "Soft Lockdown",
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    },
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    },
                ],
            },
        }


except:
    pass

#
# New fatalities Switzerland
#
try:

    @app.callback(
        Output("new-fatalities-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_new_fatalities_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_fatalities_by_date_diff[:-3].index,
                    "y": data.swiss_fatalities_by_date_diff[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_fatalities_by_date_diff.iloc[-4:].index,
                    "y": data.swiss_fatalities_by_date_diff.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(44, 254, 193, 0.25)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_daily_fatalities_country_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_daily_fatalities_country_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_daily_fatalities_country_y"][lang].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "line",
                        "xref": "x",
                        "yref": "paper",
                        "x0": "2020-03-16",
                        "y0": 0,
                        "x1": "2020-03-16",
                        "y1": 1,
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
                    },
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    },
                ],
                "annotations": [
                    {
                        "x": "2020-03-16",
                        "y": 0.92,
                        "xref": "x",
                        "yref": "paper",
                        "text": "Soft Lockdown",
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    },
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    },
                ],
            },
        }


except:
    pass

#
# Hospitalizations
#
try:

    @app.callback(
        Output("hospitalizations-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_hospitalizations_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_hospitalizations[:-3]["Date"],
                    "y": data.swiss_hospitalizations[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_regular"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["yellow"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_icu[:-3]["Date"],
                    "y": data.swiss_icu[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_intensive"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["red"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_vent[:-3]["Date"],
                    "y": data.swiss_vent[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_ventilated"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["blue"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_hospitalizations.iloc[-4:]["Date"],
                    "y": data.swiss_hospitalizations.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_regular"][lang].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(254, 211, 48, 0.2)"},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_icu.iloc[-4:]["Date"],
                    "y": data.swiss_icu.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_intensive"][lang].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(252, 92, 101, 0.2)"},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_vent.iloc[-4:]["Date"],
                    "y": data.swiss_vent.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_ventilated"][lang].get(),
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(69, 170, 242, 0.2)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_hospitalizations_country_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_hospitalizations_country_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_hospitalizations_country_y"][lang].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    }
                ],
                "annotations": [
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    }
                ],
            },
        }


except:
    pass

try:

    @app.callback(
        Output("releases-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_releases_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_releases[:-3]["Date"],
                    "y": data.swiss_releases[:-3][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": "Regular",
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_releases.iloc[-4:]["Date"],
                    "y": data.swiss_releases.iloc[-4:][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": "Regular",
                    "mode": "lines",
                    "line": {"dash": "dot"},
                    "marker": {"color": "rgba(44, 254, 193, 0.25)"},
                    "showlegend": False,
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_releases_country_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_releases_country_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_releases_country_y"][lang].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#1d2533",
                        "opacity": 1.0,
                        "layer": "below",
                        "line": {"width": 0},
                    }
                ],
                "annotations": [
                    {
                        "x": data.swiss_cases_by_date_diff.index[-3],
                        "y": 0.95,
                        "xref": "x",
                        "yref": "paper",
                        "text": cfg["i18n"]["incomplete_data"][lang].get(),
                        "font": {"color": style.theme["accent"]},
                        "align": "left",
                        "showarrow": True,
                        "arrowhead": 2,
                        "arrowsize": 1,
                        "arrowwidth": 1,
                        "arrowcolor": style.theme["accent"],
                    }
                ],
            },
        }


except:
    pass

#
# Log-Log Plot Coutnry
#
try:

    @app.callback(
        Output("caseincrease-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_caseincrease_ch_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_cases.iloc[6:-1][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "y": data.moving_total[cfg["settings"]["total_column_name"].get()][
                        6:-1
                    ],
                    "mode": "lines+markers",
                    "name": cfg["i18n"]["plot_loglog_country_weekly"][lang].get(),
                    "marker": {"color": style.theme["foreground"]},
                    "text": data.moving_total["date_label"][6:-1],
                    "hovertemplate": cfg["i18n"][
                        "plot_log_log_country_weekly_hovertemplate"
                    ][lang].get(),
                },
                {
                    "x": data.swiss_cases.iloc[6:-1][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "y": data.swiss_cases_by_date_diff[
                        cfg["settings"]["total_column_name"].get()
                    ][6:-1],
                    "mode": "lines+markers",
                    "name": cfg["i18n"]["plot_loglog_country_daily"][lang].get(),
                    "marker": {"color": style.theme["yellow"]},
                    "text": data.swiss_cases_by_date_diff["date_label"][6:-1],
                    "hovertemplate": cfg["i18n"][
                        "plot_log_log_country_daily_hovertemplate"
                    ][lang].get(),
                },
            ],
            "layout": {
                "title": cfg["i18n"]["plot_loglog_country_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_loglog_country_x"][lang].get(),
                    "type": "log",
                },
                "yaxis": {
                    "type": "log",
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_loglog_country_y"][lang].get(),
                },
                "legend": {
                    "x": 0.015,
                    "y": 1,
                    "traceorder": "normal",
                    "font": {"family": "sans-serif", "color": "white"},
                    "bgcolor": style.theme["background"],
                    "bordercolor": style.theme["accent"],
                    "borderwidth": 1,
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

#
# Total cases world
#
try:

    @app.callback(
        Output("case-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_case_world_graph(selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_world_cases_normalized.index.values,
                    "y": data.swiss_world_cases_normalized[country],
                    "name": country,
                    # "marker": {"color": theme["foreground"]},
                    # "type": "bar",
                }
                for country in data.swiss_world_cases_normalized
                if country != "Day"
            ],
            "layout": {
                "title": cfg["i18n"]["plot_world_cases_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_cases_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_cases_y"][lang].get(),
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

try:

    @app.callback(
        Output("fatalities-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_fatalities_world_graph(selected_scale):
        return {
            "data": [
                {
                    "x": ["Switzerland"]
                    + data.world_case_fatality_rate.index.values.tolist(),
                    "y": [data.swiss_case_fatality_rate]
                    + [val for val in data.world_case_fatality_rate],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "marker": {"color": style.theme["foreground"]},
                    "type": "bar",
                }
            ],
            "layout": {
                "title": cfg["i18n"]["plot_world_cfr_title"][lang].get(),
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_cfr_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_world_cfr_y"][lang].get(),
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

#
# BAG Data
#
try:

    @app.callback(
        Output("cases-bag-graph", "figure"),
        [Input("select-regions-ch", "value"), Input("radio-absolute-norm", "value")],
    )
    def update_cases_bag_graph(region, norm):
        field = "cases"
        factor = 1
        title = cfg["i18n"]["plot_age_dist_abs_title"][lang].get()
        ytitle = cfg["i18n"]["plot_age_dist_abs_y"][lang].get()

        if norm == "scaled":
            field = "cases_pp"
            factor = 100
            title = cfg["i18n"]["plot_age_dist_scaled_title"][lang].get()
            ytitle = cfg["i18n"]["plot_age_dist_scaled_y"][lang].get()

        return {
            "data": [
                {
                    "x": data.age_data_male_hist[
                        data.age_data_male_hist["region"] == region
                    ]["age"],
                    "y": data.age_data_male_hist[
                        data.age_data_male_hist["region"] == region
                    ][field]
                    * factor,
                    "name": cfg["i18n"]["male"][lang].get(),
                    # "mode": "lines",
                    "type": "bar",
                    "line": {"width": 2.0, "color": "rgba(255, 5, 71, 1)",},
                    "marker": {"color": "rgba(255, 5, 71, 0.5)"},
                },
                {
                    "x": data.age_data_female_hist[
                        data.age_data_female_hist["region"] == region
                    ]["age"],
                    "y": data.age_data_female_hist[
                        data.age_data_female_hist["region"] == region
                    ][field]
                    * factor,
                    "name": cfg["i18n"]["female"][lang].get(),
                    # "mode": "lines",
                    "type": "bar",
                    "line": {"width": 2.0, "color": "rgba(56, 206, 255, 1)",},
                    "marker": {"color": "rgba(56, 206, 255, 0.5)"},
                },
            ],
            "layout": {
                "title": title,
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_age_dist_x"][lang].get(),
                },
                "yaxis": {
                    "type": "linear",
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": ytitle,
                },
                "barmode": "overlay",
                # "barmode": "stack",
                "bargap": 0,
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background_secondary"],
                "paper_bgcolor": style.theme["background_secondary"],
                "font": {"color": style.theme["foreground_secondary"]},
            },
        }


except:
    pass

try:

    @app.callback(
        Output("fatalities-bag-graph", "figure"),
        [Input("select-regions-ch", "value"), Input("radio-absolute-norm", "value")],
    )
    def update_fatalities_bag_graph(region, norm):
        field = "fatalities"
        factor = 1
        title = cfg["i18n"]["plot_age_dist_fatalities_abs_title"][lang].get()
        ytitle = cfg["i18n"]["plot_age_dist_fatalities_abs_y"][lang].get()

        if norm == "scaled":
            field = "fatalities_pp"
            factor = 100
            title = cfg["i18n"]["plot_age_dist_fatalities_scaled_title"][lang].get()
            ytitle = cfg["i18n"]["plot_age_dist_fatalities_scaled_y"][lang].get()

        return {
            "data": [
                {
                    "x": data.age_data_male_hist[
                        data.age_data_male_hist["region"] == region
                    ]["age"],
                    "y": data.age_data_male_hist[
                        data.age_data_male_hist["region"] == region
                    ][field]
                    * factor,
                    "name": cfg["i18n"]["male"][lang].get(),
                    # "mode": "lines",
                    "type": "bar",
                    "line": {"width": 2.0, "color": "rgba(255, 5, 71, 1)",},
                    "marker": {"color": "rgba(255, 5, 71, 0.5)"},
                },
                {
                    "x": data.age_data_female_hist[
                        data.age_data_female_hist["region"] == region
                    ]["age"],
                    "y": data.age_data_female_hist[
                        data.age_data_female_hist["region"] == region
                    ][field]
                    * factor,
                    "name": cfg["i18n"]["female"][lang].get(),
                    # "mode": "lines",
                    "type": "bar",
                    "line": {"width": 2.0, "color": "rgba(56, 206, 255, 1)",},
                    "marker": {"color": "rgba(56, 206, 255, 0.5)"},
                },
            ],
            "layout": {
                "title": title,
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_age_dist_fatalities_x"][lang].get(),
                },
                "yaxis": {
                    "type": "linear",
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": ytitle,
                },
                "barmode": "overlay",
                # "barmode": "stack",
                "bargap": 0,
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background_secondary"],
                "paper_bgcolor": style.theme["background_secondary"],
                "font": {"color": style.theme["foreground_secondary"]},
            },
        }


except:
    pass

#
# regional Data
#
try:

    @app.callback(
        Output("case-graph", "figure"),
        [Input("dropdown-regions", "value"), Input("radio-scale-regions", "value")],
    )
    def update_case_graph(selected_regions, selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_cases_as_dict["Date"],
                    "y": data.swiss_cases_as_dict[region],
                    "name": region,
                    "marker": {"color": style.region_colors[region]},
                }
                for _, region in enumerate(data.swiss_cases_as_dict)
                if region in selected_regions
            ],
            "layout": {
                "title": cfg["i18n"]["plot_cases_regional_title"][lang].get(),
                "height": 750,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_regional_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_regional_y"][lang].get(),
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

try:

    @app.callback(
        Output("case-pc-graph", "figure"),
        [Input("dropdown-regions", "value"), Input("radio-scale-regions", "value")],
    )
    def update_case_pc_graph(selected_regions, selected_scale):
        return {
            "data": [
                {
                    "x": data.swiss_cases_normalized_as_dict["Date"],
                    "y": data.swiss_cases_normalized_as_dict[region],
                    "name": region,
                    "marker": {"color": style.region_colors[region]},
                }
                for _, region in enumerate(data.swiss_cases_normalized_as_dict)
                if region in selected_regions
            ],
            "layout": {
                "title": cfg["i18n"]["plot_cases_pc_regional_title"][lang].get(),
                "height": 750,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_pc_regional_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_pc_regional_y"][lang].get(),
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

try:

    @app.callback(
        Output("case-graph-diff", "figure"),
        [Input("dropdown-regions", "value"), Input("radio-scale-regions", "value")],
    )
    def update_case_graph_diff(selected_regions, selected_scale):
        data_non_nan = {}
        data_non_nan["Date"] = data.swiss_cases_as_dict["Date"]

        for region in data.swiss_cases_as_dict:
            if region == "Date":
                continue
            values = []
            last_value = 0
            for _, v in enumerate(data.swiss_cases_as_dict[region]):
                if math.isnan(float(v)):
                    values.append(last_value)
                else:
                    last_value = v
                    values.append(v)
            data_non_nan[region] = values

        return {
            "data": [
                {
                    "x": data_non_nan["Date"],
                    "y": [0]
                    + [
                        j - i
                        for i, j in zip(
                            data_non_nan[region][:-1], data_non_nan[region][1:]
                        )
                    ],
                    "name": region,
                    "marker": {"color": style.region_colors[region]},
                    "type": "bar",
                }
                for i, region in enumerate(data.swiss_cases_as_dict)
                if region in selected_regions
            ],
            "layout": {
                "title": cfg["i18n"]["plot_cases_new_regional_title"][lang].get(),
                "height": 750,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_new_regional_x"][lang].get(),
                },
                "yaxis": {
                    "type": "linear",
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_cases_new_regional_y"][lang].get(),
                },
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "barmode": "stack",
            },
        }


except:
    pass

try:
    app.clientside_callback(
        ClientsideFunction(
            namespace="clientside", function_name="update_caseincrease_regional_graph"
        ),
        Output("caseincrease-regional-graph", "figure"),
        [
            Input("dropdown-regions", "value"),
            Input("radio-scale-regions", "value"),
            Input("slider-date-regional", "value"),
            Input("caseincrease-regional-graph", "hoverData"),
            Input("caseincrease-regional-data", "children"),
        ],
    )
except:
    pass

try:

    @app.callback(
        Output("caseincrease-regional-data", "children"), [Input("url", "pathname")]
    )
    def store_caseincrease_regional_data(value):
        return (
            '{"swiss_cases_by_date_filled": '
            + data.swiss_cases_by_date_filled.to_json(
                date_format="iso", orient="columns"
            )
            + ', "moving_total":'
            + data.moving_total.to_json(date_format="iso", orient="columns")
            + ', "i18n": {'
            + '"plot_loglog_region_title": "'
            + cfg["i18n"]["plot_loglog_region_title"][lang].get()
            + '",'
            + '"plot_loglog_region_x": "'
            + cfg["i18n"]["plot_loglog_region_x"][lang].get()
            + '",'
            + '"plot_loglog_region_y": "'
            + cfg["i18n"]["plot_loglog_region_y"][lang].get()
            + '",'
            + '"plot_log_log_region_weekly_hovertemplate": "'
            + cfg["i18n"]["plot_log_log_region_weekly_hovertemplate"][lang].get()
            + '"}}'
        )


except:
    pass

#
# Demographic Correlations
#
try:

    @app.callback(
        Output("prevalence-density-graph", "figure"),
        [Input("dropdown-regions", "value")],
    )
    def update_prevalence_density_graph(selected_regions):
        return {
            "data": [
                {
                    "x": data.prevalence_density_regression["x"],
                    "y": data.prevalence_density_regression["y"],
                    "mode": "lines",
                    "hoverinfo": "skip",
                    "showlegend": False,
                    "line": {"dash": "dash", "width": 2.0, "color": "#ffffff",},
                }
            ]
            + [
                {
                    "x": [data.regional_demography["Density"][region]],
                    "y": [data.swiss_cases_by_date_filled_per_capita.iloc[-1][region]],
                    "name": region,
                    "mode": "markers",
                    "text": region,
                    "marker": {
                        "color": style.region_colors[region],
                        "size": data.scaled_cases[region],
                    },
                    "hoverinfo": "text",
                    "hovertext": f"<span style='font-size:2.0em'><b>{region}</b></span><br>"
                    + f"{cfg['i18n']['prevalence'][lang].get()}: <b>{data.swiss_cases_by_date_filled_per_capita.iloc[-1][region]:.3f}</b><br>"
                    + f"{cfg['i18n']['population_density'][lang].get()}: <b>{data.regional_demography['Density'][region]:.0f}</b> Inhabitants / km<sup>2</sup><br>"
                    + f"{cfg['i18n']['cases'][lang].get()}: <b>{data.swiss_cases_by_date_filled.iloc[-1][region]:.0f}</b>",
                }
                for _, region in enumerate(data.swiss_cases_as_dict)
                if region in selected_regions
            ],
            "layout": {
                "title": cfg["i18n"]["plot_corr_density_title"][lang].get(),
                "hovermode": "closest",
                "height": 750,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_corr_density_x"][lang].get(),
                },
                "yaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_corr_density_y"][lang].get(),
                },
                "annotations": [
                    {
                        "x": data.prevalence_density_regression["x"][1],
                        "y": data.prevalence_density_regression["y"][1],
                        "xref": "x",
                        "yref": "y",
                        "text": "r: "
                        + str(round(data.prevalence_density_regression["r_value"], 2))
                        + "<br>"
                        + "p-value: "
                        + str(round(data.prevalence_density_regression["p_value"], 2)),
                        "showarrow": True,
                        "arrowhead": 4,
                        "ax": 50,
                        "ay": 50,
                        "font": {"size": 12, "color": "#ffffff",},
                        "arrowcolor": "#ffffff",
                        "align": "left",
                    }
                ],
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

try:

    @app.callback(
        Output("cfr-age-graph", "figure"), [Input("dropdown-regions", "value")],
    )
    def update_cfr_age_graph(selected_regions):
        return {
            "data": [
                {
                    "x": [v * 100 for v in data.cfr_age_regression["x"]],
                    "y": data.cfr_age_regression["y"],
                    "mode": "lines",
                    "hoverinfo": "skip",
                    "showlegend": False,
                    "line": {"dash": "dash", "width": 2.0, "color": "#ffffff",},
                }
            ]
            + [
                {
                    "x": [data.regional_demography["O65"][region] * 100],
                    "y": [data.swiss_case_fatality_rates.iloc[-1][region]],
                    "name": region,
                    "mode": "markers",
                    "marker": {
                        "color": style.region_colors[region],
                        "size": data.scaled_cases[region],
                    },
                    "hoverinfo": "text",
                    "hovertext": f"<span style='font-size:2.0em'><b>{region}</b></span><br>"
                    + f"{cfg['i18n']['population_over_65'][lang].get()}: <b>{data.regional_demography['O65'][region] * 100:.0f}%</b><br>"
                    + f"{cfg['i18n']['case_fatality_ratio'][lang].get()}: <b>{data.swiss_case_fatality_rates.iloc[-1][region]:.3f}</b><br>"
                    + f"{cfg['i18n']['cases'][lang].get()}: <b>{data.swiss_cases_by_date_filled.iloc[-1][region]:.0f}</b>",
                }
                for _, region in enumerate(data.swiss_cases_normalized_as_dict)
                if region in selected_regions
            ],
            "layout": {
                "title": cfg["i18n"]["plot_corr_age_title"][lang].get(),
                "hovermode": "closest",
                "height": 750,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_corr_age_x"][lang].get(),
                },
                "yaxis": {
                    "type": "linear",
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_corr_age_y"][lang].get(),
                },
                "annotations": [
                    {
                        "x": data.cfr_age_regression["x"][1] * 100,
                        "y": data.cfr_age_regression["y"][1],
                        "xref": "x",
                        "yref": "y",
                        "text": "r: "
                        + str(round(data.cfr_age_regression["r_value"], 2))
                        + "<br>"
                        + "p-value: "
                        + str(round(data.cfr_age_regression["p_value"], 2)),
                        "showarrow": True,
                        "arrowhead": 4,
                        "ax": -50,
                        "ay": -50,
                        "font": {"size": 12, "color": "#ffffff",},
                        "arrowcolor": "#ffffff",
                        "align": "left",
                    }
                ],
                "dragmode": False,
                "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass


# Kick off the updated thread
executor = ThreadPoolExecutor(max_workers=1)
executor.submit(update_data)

if __name__ == "__main__":
    app.run_server(
        # debug=True,
        # dev_tools_hot_reload=True,
        # dev_tools_hot_reload_interval=50,
        # dev_tools_hot_reload_max_retry=30,
    )
