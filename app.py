import time
import numpy as np
from dashcoch import DataLoader, StyleLoader
import math
from datetime import date, datetime, timedelta
import json
import geojson
import flask
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ClientsideFunction
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dashcoch.config import config as cfg
from flask_caching import Cache


external_scripts = [
    "https://cdn.simpleanalytics.io/hello.js",
]

lang = 0

meta_tags = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
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
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=meta_tags,
)
server = app.server

app.title = cfg["i18n"]["title"][lang].get()
style = StyleLoader(cfg)

def get_data():
    global data
    try:
        data = DataLoader(cfg)
    except:
        pass


def update_data(period=int(cfg["settings"]["update_interval"].get())):
    while True:
        get_data()
        print("Data updated at " + datetime.now().isoformat())
        time.sleep(period)


get_data()


def get_lang():
    try:
        if not flask.has_request_context():
            return cfg["settings"]["default_language"].get()

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

    except:
        lang = cfg["settings"]["default_language"].get()


# -------------------------------------------------------------------------------
# Globals used by Callbacks
# -------------------------------------------------------------------------------
phase_shapes = [
    # {
    #     "type": "line",
    #     "xref": "x",
    #     "yref": "paper",
    #     "x0": "2020-03-16",
    #     "y0": 0,
    #     "x1": "2020-03-16",
    #     "y1": 1,
    #     "opacity": 1.0,
    #     "layer": "below",
    #     "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
    # },
    # {
    #     "type": "line",
    #     "xref": "x",
    #     "yref": "paper",
    #     "x0": "2020-04-27",
    #     "y0": 0,
    #     "x1": "2020-04-27",
    #     "y1": 1,
    #     "opacity": 1.0,
    #     "layer": "below",
    #     "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
    # },
    {
        "type": "line",
        "xref": "x",
        "yref": "paper",
        "x0": "2020-05-11",
        "y0": 0,
        "x1": "2020-05-11",
        "y1": 1,
        "opacity": 1.0,
        "layer": "below",
        "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
    },
    {
        "type": "line",
        "xref": "x",
        "yref": "paper",
        "x0": "2020-06-06",
        "y0": 0,
        "x1": "2020-06-06",
        "y1": 1,
        "opacity": 1.0,
        "layer": "below",
        "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
    },
    {
        "type": "line",
        "xref": "x",
        "yref": "paper",
        "x0": "2020-06-22",
        "y0": 0,
        "x1": "2020-06-22",
        "y1": 1,
        "opacity": 1.0,
        "layer": "below",
        "line": {"width": 1.0, "color": "#ffffff", "dash": "dash",},
    },
]
phase_annotations = [
    # {
    #     "x": "2020-04-06",
    #     "y": -0.12,
    #     "xref": "x",
    #     "yref": "paper",
    #     "text": "Soft Lockdown",
    #     "font": {"color": "#ffffff"},
    #     "align": "center",
    #     "showarrow": False,
    # },
    # {
    #     "x": "2020-05-04",
    #     "y": -0.12,
    #     "xref": "x",
    #     "yref": "paper",
    #     "text": "Phase I",
    #     "font": {"color": "#ffffff"},
    #     "align": "center",
    #     "showarrow": False,
    # },
    {
        "x": "2020-05-24",
        "y": -0.12,
        "xref": "x",
        "yref": "paper",
        "text": "Phase II",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    },
    {
        "x": "2020-06-14",
        "y": -0.12,
        "xref": "x",
        "yref": "paper",
        "text": "Phase III",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    }
]

phase_annotations_double_height = [
    {
        "x": "2020-04-06",
        "y": -0.06,
        "xref": "x",
        "yref": "paper",
        "text": "Soft Lockdown",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    },
    {
        "x": "2020-05-04",
        "y": -0.06,
        "xref": "x",
        "yref": "paper",
        "text": "Phase I",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    },
    {
        "x": "2020-05-24",
        "y": -0.06,
        "xref": "x",
        "yref": "paper",
        "text": "Phase II",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    },
    {
        "x": "2020-06-14",
        "y": -0.06,
        "xref": "x",
        "yref": "paper",
        "text": "Phase III",
        "font": {"color": "#ffffff"},
        "align": "center",
        "showarrow": False,
    }
]

def get_layout():
    lang = get_lang()
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
                        html.Div(id="muy-importante", children=[dcc.Markdown(cfg["i18n"]["important"][lang].get())]),
                        dbc.Button(
                            "Info",
                            id="info-button",
                            size="sm",
                            className="mb-3",
                            color="primary",
                        ),
                        dbc.Collapse(
                            id="info-container",
                            children=[
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
                                        [
                                            dcc.Markdown(
                                                cfg["i18n"]["more_info"][lang].get()
                                            )
                                        ]
                                        if cfg["show"]["more_info"].get()
                                        else []
                                    ),
                                ),
                            ],
                        ),
                        html.Br(),
                    ],
                ),
            ]
        )

    # Totals
    if cfg["show"]["totals"]:
        content.extend(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                className="total-container",
                                children=[
                                    html.P(
                                        className="total-title",
                                        children=cfg["i18n"]["total_reported_cases"][
                                            lang
                                        ].get(),
                                    ),
                                    html.Div(
                                        className="total-content",
                                        children=str(int(data.total_swiss_cases)),
                                    ),
                                ],
                            ),
                            lg=3,
                            md=6,
                            xs=6,
                        ),
                        dbc.Col(
                            html.Div(
                                className="total-container",
                                children=[
                                    html.P(
                                        className="total-title",
                                        children=cfg["i18n"]["reported_cases_today"][
                                            lang
                                        ].get(),
                                    ),
                                    html.Div(
                                        className="total-content",
                                        children="+" + str(int(data.new_swiss_cases)),
                                    ),
                                ],
                            ),
                            lg=3,
                            md=6,
                            xs=6,
                        ),
                        dbc.Col(
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
                                        children=str(int(data.total_swiss_fatalities)),
                                    ),
                                ],
                            ),
                            lg=3,
                            md=6,
                            xs=6,
                        ),
                        dbc.Col(
                            html.Div(
                                className="total-container",
                                children=[
                                    html.P(
                                        className="total-title",
                                        children=cfg["i18n"]["regions_updated_today"][
                                            lang
                                        ].get(),
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
                            lg=3,
                            md=6,
                            xs=6,
                        ),
                    ]
                ),
                html.Br(),
            ]
        )

    # Updated regions
    if cfg["show"]["updates"]:
        content.extend(
            [
                html.Div(
                    className="update-container",
                    children=[
                        html.Div(
                            className="update-title",
                            children=cfg["i18n"]["latest_updates"][lang].get(),
                        ),
                        html.Div(
                            className="update-content",
                            children=[
                                html.Span(
                                    className=str(vals["Updated_Today"]),
                                    children=region
                                    + ": "
                                    + date.fromisoformat(vals["Date"]).strftime(
                                        "%d. %m."
                                    )
                                    + " "
                                    + vals["Time"],
                                )
                                for region, vals in data.last_updated.iterrows()
                            ],
                        ),
                    ],
                ),
            ]
        )

    # Map
    if cfg["show"]["map"]:
        content.extend(
            [
                html.Div(id="map-data", style={"display": "none"}),
                html.Div(id="date-container", className="slider-container"),
                html.Div(
                    children=[
                        dcc.Graph(
                            id="update-map",
                            config={"staticPlot": True},
                            style={"height": "62vw", "maxHeight": "600px"},
                        ),
                    ],
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.RadioItems(
                                    id="map-radios",
                                    options=[
                                        {
                                            "label": cfg["i18n"]["new_cases"][
                                                lang
                                            ].get(),
                                            "value": "new",
                                        },
                                        {
                                            "label": cfg["i18n"][
                                                "total_reported_cases"
                                            ][lang].get(),
                                            "value": "number",
                                        },
                                        {
                                            "label": cfg["i18n"][
                                                "cumulative_prevalence"
                                            ][lang].get(),
                                            "value": "prevalence",
                                        },
                                        {
                                            "label": cfg["i18n"][
                                                "new_hospitalizations"
                                            ][lang].get(),
                                            "value": "new_hospitalizations",
                                        },
                                        {
                                            "label": cfg["i18n"][
                                                "total_hospitalizations"
                                            ][lang].get(),
                                            "value": "hospitalizations",
                                        },
                                        {
                                            "label": cfg["i18n"]["new_fatalities"][
                                                lang
                                            ].get(),
                                            "value": "new_fatalities",
                                        },
                                        {
                                            "label": cfg["i18n"]["total_fatalities"][
                                                lang
                                            ].get(),
                                            "value": "fatalities",
                                        },
                                    ],
                                    value="new",
                                    inline=True,
                                ),
                            ]
                        ),
                    )
                ),
                html.Div(
                    id="map-slider",
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
            ]
        )

    if cfg["show"]["region_overview"]:
        content.extend([
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                className="plot-title",
                                children=cfg["i18n"]["plot_regional_overview_title"][lang].get()
                            ),
                            dcc.Graph(
                                id="region-boxes", config={"displayModeBar": False}
                            ),
                        ],
                        md=12,
                        lg=12,
                    )
                ]
            ),
        ])

    # Links to regional websites
    if cfg["show"]["region_links"]:
        content.extend(
            [
                html.Div(
                    className="plot-title",
                    children=cfg["i18n"]["regional_data"][lang].get(),
                ),
                html.Div(
                    id="regional-links-container",
                    children=[
                        html.A(children=region["region"], href=region["detail"])
                        for region in cfg["regions"].get()
                        if "detail" in region
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
                    children=cfg["i18n"]["info_main"][lang].get(),
                ),
                html.Div(
                    className="plot-settings-container",
                    children=[
                        dbc.FormGroup(
                            [
                                dbc.RadioItems(
                                    id="radio-scale-switzerland",
                                    options=[
                                        {
                                            "label": cfg["i18n"]["linear_scale"][
                                                lang
                                            ].get(),
                                            "value": "linear",
                                        },
                                        {
                                            "label": cfg["i18n"]["log_scale"][
                                                lang
                                            ].get(),
                                            "value": "log",
                                        },
                                    ],
                                    value="linear",
                                    inline=True,
                                ),
                            ]
                        )
                    ],
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_total_reported_cases_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="case-ch-graph", config={"displayModeBar": False}
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_total_fatalities_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="fatalities-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                    ],
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_daily_reported_cases_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="new-case-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_daily_fatalities_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="new-fatalities-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
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
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_hospitalizations_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="hospitalizations-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_releases_country_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="releases-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                    ]
                ),
                html.Br(),
            ]
        )

    if cfg["show"]["hospitalizations"] and not cfg["show"]["hospital_releases"]:
        content.extend(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_hospitalizations_country_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="hospitalizations-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        )
                    ]
                ),
                html.Br(),
            ]
        )

    # Log-Log Development Plot
    if cfg["show"]["log_log_development"]:
        content.extend(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_loglog_country_title"][
                                        lang
                                    ].get(),
                                ),
                                html.Div(
                                    className="info-container",
                                    children=cfg["i18n"]["info_log_log_main"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="caseincrease-ch-graph",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        )
                    ]
                ),
                html.Br(),
            ]
        )

    # Age Distribution
    if cfg["show"]["tests"]:
        content.extend(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_tests_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="tests-graph",
                                    figure={
                                        "data": [
                                            {
                                                "x": data.tests.index,
                                                "y": data.tests["neg"],
                                                "name": cfg["i18n"]["plot_tests_neg"][lang].get(),
                                                "mode": "lines",
                                                "marker": {"color": style.theme["green"]},
                                            },
                                            {
                                                "x": data.tests.index,
                                                "y": data.tests["pos"],
                                                "name": cfg["i18n"]["plot_tests_pos"][lang].get(),
                                                "mode": "lines",
                                                "marker": {"color": style.theme["red"]},
                                            },
                                        ],
                                        "layout": {
                                            "height": 400,
                                            "xaxis": {
                                                "showgrid": True,
                                                "color": "#ffffff",
                                                "title": cfg["i18n"]["plot_tests_x"][lang].get(),
                                            },
                                            "yaxis": {
                                                "type": "linear",
                                                "showgrid": True,
                                                "color": "#ffffff",
                                                "rangemode": "tozero",
                                                "title": cfg["i18n"]["plot_tests_y"][lang].get(),
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
                                            "hovermode": "x unified",
                                            "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                                            "plot_bgcolor": style.theme["background"],
                                            "paper_bgcolor": style.theme["background"],
                                            "font": {"color": style.theme["foreground"]},
                                            "shapes": phase_shapes,
                                            "annotations": phase_annotations,
                                        },
                                    },
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_tests_ratio_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="tests-ratio-graph",
                                    figure={
                                        "data": [
                                            {
                                                "x": data.tests.index,
                                                "y": data.tests["pos_rate"],
                                                "type": "bar",
                                                "marker": {"color": style.theme["foreground"], "opacity": 0.5},
                                                "hovertemplate": "%{y} %<extra></extra>",
                                                "showlegend": False,
                                            },
                                            {
                                                "x": data.tests.index,
                                                "y": data.tests["pos_rate_rolling"],
                                                "mode": "lines",
                                                "marker": {"color": style.theme["foreground"]},
                                                "name": cfg["i18n"]["moving_average"][lang].get(),
                                                "hovertemplate": "%{y} %<extra></extra>",
                                                "showlegend": True,
                                                "fill": "tozeroy",
                                            }
                                        ],
                                        "layout": {
                                            "height": 400,
                                            "xaxis": {
                                                "showgrid": True,
                                                "color": "#ffffff",
                                                "title": cfg["i18n"]["plot_tests_ratio_x"][lang].get(),
                                            },
                                            "yaxis": {
                                                "type": "linear",
                                                "showgrid": True,
                                                "color": "#ffffff",
                                                "rangemode": "tozero",
                                                "title": cfg["i18n"]["plot_tests_ratio_y"][lang].get(),
                                            },
                                            "legend": {
                                                "x": 0.015,
                                                "y": 0.9,
                                                "traceorder": "normal",
                                                "font": {"family": "sans-serif", "color": "white"},
                                                "bgcolor": style.theme["background"],
                                                "bordercolor": style.theme["accent"],
                                                "borderwidth": 1,
                                            },
                                            "dragmode": False,
                                            "hovermode": "x unified",
                                            "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                                            "plot_bgcolor": style.theme["background"],
                                            "paper_bgcolor": style.theme["background"],
                                            "font": {"color": style.theme["foreground"]},
                                            "shapes": phase_shapes,
                                            "annotations": phase_annotations,
                                        },
                                    },
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                    ]
                ),
                html.Br(),
            ]
        )

    # International Data
    if cfg["show"]["international"]:
        content.extend(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_world_cases_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="cases-world-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_world_fatalities_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="fatalities-world-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_world_tests_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="new-tests-world-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_world_positivity_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="test-positivity-world-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=6,
                        )
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_tests_vs_positivity_title"][
                                        lang
                                    ].get(),
                                ),
                                html.Div(
                                    className="info-container",
                                    children=cfg["i18n"]["info_plot_tests_vs_positivity"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="tests-vs-positivity-world-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=12,
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
                    children=cfg["i18n"]["info_age_distribution"][lang].get(),
                ),
                html.Div(
                    className="plot-settings-container",
                    children=[
                        html.P(
                            className="slider-text",
                            children=cfg["i18n"]["show_data_for"][lang].get(),
                        ),
                        dbc.FormGroup(
                            [
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
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="plot-settings-container",
                    children=[
                        dbc.FormGroup(
                            [
                                dbc.RadioItems(
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
                                    inline=True,
                                ),
                            ]
                        )
                    ],
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="age-dist-cases-title", className="plot-title",
                                ),
                                dcc.Graph(
                                    id="cases-bag-graph",
                                    config={"displayModeBar": False,},
                                ),
                            ],
                            md=12,
                            lg=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="age-dist-fatalities-title",
                                    className="plot-title",
                                ),
                                dcc.Graph(
                                    id="fatalities-bag-graph",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            md=12,
                            lg=12,
                        )
                    ]
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
                    children=cfg["i18n"]["info_regional"][lang].get(),
                ),
                html.Div(
                    className="plot-settings-container",
                    children=[
                        dbc.FormGroup(
                            [
                                dbc.RadioItems(
                                    id="radio-scale-regions",
                                    options=[
                                        {
                                            "label": cfg["i18n"]["linear_scale"][
                                                lang
                                            ].get(),
                                            "value": "linear",
                                        },
                                        {
                                            "label": cfg["i18n"]["log_scale"][
                                                lang
                                            ].get(),
                                            "value": "log",
                                        },
                                    ],
                                    value="linear",
                                    inline=True,
                                ),
                            ]
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
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_cases_regional_title"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="case-graph", config={"displayModeBar": False}
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_cases_pc_regional_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="case-pc-graph", config={"displayModeBar": False}
                                ),
                            ],
                            md=12,
                            lg=6,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"][
                                        "plot_cases_new_regional_title"
                                    ][lang].get(),
                                ),
                                dcc.Graph(
                                    id="case-graph-diff",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        )
                    ]
                ),
                html.Br(),
            ]
        )

    # Regional Log-Log Development Plot
    if cfg["show"]["log_log_regional_development"]:
        content.extend(
            [
                html.Div(id="caseincrease-regional-data", style={"display": "none"}),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    className="plot-title",
                                    children=cfg["i18n"]["plot_loglog_region_title"][
                                        lang
                                    ].get(),
                                ),
                                html.Div(
                                    className="info-container",
                                    children=cfg["i18n"]["info_log_log_regional"][
                                        lang
                                    ].get(),
                                ),
                                dcc.Graph(
                                    id="caseincrease-regional-graph",
                                    config={"displayModeBar": False},
                                ),
                            ]
                        )
                    ]
                ),
                html.Div(
                    id="map-slider-regional",
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
                            marks={
                                i: date.fromisoformat(d).strftime("%d. %m.")
                                for i, d in enumerate(data.swiss_cases["Date"])
                                if date.fromisoformat(d).weekday() == 0
                            },
                            value=len(data.moving_total) - 1,
                            updatemode="drag",
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

    return dbc.Container(id="main", children=content, fluid=True)


app.layout = get_layout


# -------------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------------
try:

    @app.callback(
        Output("info-container", "is_open"),
        [Input("info-button", "n_clicks")],
        [State("info-container", "is_open")],
    )
    def toggle_info(n, is_open):
        if n:
            return not is_open
        return is_open


except:
    pass

try:

    @app.callback(
        Output("date-container", "children"), [Input("slider-date", "value")],
    )
    def update_map_date(selected_date_index):

        d = date.fromisoformat(data.swiss_cases["Date"].iloc[selected_date_index])
        return d.strftime("%d. %m. %Y")


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
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.swiss_cases["Date"],
                    "y": data.swiss_cases[cfg["settings"]["total_column_name"].get()],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                }
            ],
            "layout": {
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "above",
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
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.swiss_fatalities["Date"],
                    "y": data.swiss_fatalities[
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["settings"]["total_column_name"].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
            ],
            "layout": {
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "above",
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
        lang = get_lang()
        total_column_name = cfg["settings"]["total_column_name"].get()
        return {
            "data": [
                {
                    "x": data.swiss_cases_by_date_diff.index,
                    "y": data.swiss_cases_by_date_diff[total_column_name],
                    "name": total_column_name,
                    "type": "bar",
                    "marker": {"color": style.theme["foreground"], "opacity": 0.5},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_cases_by_date_diff.index,
                    "y": data.swiss_cases_by_date_diff[total_column_name + "_rolling"],
                    "name": cfg["i18n"]["moving_average"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "fill": "tozeroy",
                },
            ],
            "layout": {
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
                "legend": {
                    "x": 0.015,
                    "y": 0.9,
                    "traceorder": "normal",
                    "font": {"family": "sans-serif", "color": "white"},
                    "bgcolor": style.theme["background"],
                    "bordercolor": style.theme["accent"],
                    "borderwidth": 1,
                },
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": phase_shapes + [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "below",
                        "line": {"width": 0},
                    },
                ],
                "annotations": phase_annotations + [
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
        lang = get_lang()
        total_column_name = cfg["settings"]["total_column_name"].get()
        return {
            "data": [
                {
                    "x": data.swiss_fatalities_by_date_diff.index,
                    "y": data.swiss_fatalities_by_date_diff[total_column_name],
                    "name": total_column_name,
                    "type": "bar",
                    "marker": {"color": style.theme["foreground"], "opacity": 0.5},
                    "showlegend": False,
                },
                {
                    "x": data.swiss_fatalities_by_date_diff.index,
                    "y": data.swiss_fatalities_by_date_diff[
                        total_column_name + "_rolling"
                    ],
                    "name": cfg["i18n"]["moving_average"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "fill": "tozeroy",
                },
            ],
            "layout": {
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
                "legend": {
                    "x": 0.015,
                    "y": 0.9,
                    "traceorder": "normal",
                    "font": {"family": "sans-serif", "color": "white"},
                    "bgcolor": style.theme["background"],
                    "bordercolor": style.theme["accent"],
                    "borderwidth": 1,
                },
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "shapes": phase_shapes + [
                    {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": data.swiss_cases_by_date_diff.index[-4],
                        "y0": 0,
                        "x1": data.swiss_cases_by_date_diff.index[-1],
                        "y1": 1,
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "below",
                        "line": {"width": 0},
                    },
                ],
                "annotations": phase_annotations + [
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
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.swiss_hospitalizations["Date"],
                    "y": data.swiss_hospitalizations[
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": cfg["i18n"]["plot_hospitalizations_regular"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["yellow"]},
                },
                {
                    "x": data.swiss_icu["Date"],
                    "y": data.swiss_icu[cfg["settings"]["total_column_name"].get()],
                    "name": cfg["i18n"]["plot_hospitalizations_intensive"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["red"]},
                },
                {
                    "x": data.swiss_vent["Date"],
                    "y": data.swiss_vent[cfg["settings"]["total_column_name"].get()],
                    "name": cfg["i18n"]["plot_hospitalizations_ventilated"][lang].get(),
                    "mode": "lines",
                    "marker": {"color": style.theme["blue"]},
                },
            ],
            "layout": {
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
                "legend": {
                    "x": 0.015,
                    "y": 1,
                    "traceorder": "normal",
                    "font": {"family": "sans-serif", "color": "white"},
                    "bgcolor": style.theme["background"],
                    "bordercolor": style.theme["accent"],
                    "borderwidth": 1,
                },
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "above",
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
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.swiss_releases["Date"],
                    "y": data.swiss_releases[
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "name": "Regular",
                    "mode": "lines",
                    "marker": {"color": style.theme["foreground"]},
                    "showlegend": False,
                },
            ],
            "layout": {
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
                        "fillcolor": "#121314",
                        "opacity": 0.75,
                        "layer": "above",
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
# Log-Log Plot Country
#
try:
    @app.callback(
        Output("caseincrease-ch-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_caseincrease_ch_graph(selected_scale):
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.swiss_cases.iloc[6:-2][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "y": data.moving_total[cfg["settings"]["total_column_name"].get()][
                        6:-2
                    ],
                    "mode": "lines+markers",
                    "name": cfg["i18n"]["plot_loglog_country_weekly"][lang].get(),
                    "marker": {"color": style.theme["foreground"]},
                    "text": data.moving_total["date_label"][6:-2],
                    "hovertemplate": cfg["i18n"][
                        "plot_log_log_country_weekly_hovertemplate"
                    ][lang].get(),
                },
                {
                    "x": data.swiss_cases.iloc[6:-2][
                        cfg["settings"]["total_column_name"].get()
                    ],
                    "y": data.swiss_cases_by_date_diff[
                        cfg["settings"]["total_column_name"].get()
                    ][6:-2],
                    "mode": "lines+markers",
                    "name": cfg["i18n"]["plot_loglog_country_daily"][lang].get(),
                    "marker": {"color": style.theme["yellow"]},
                    "text": data.swiss_cases_by_date_diff["date_label"][6:-2],
                    "hovertemplate": cfg["i18n"][
                        "plot_log_log_country_daily_hovertemplate"
                    ][lang].get(),
                },
            ],
            "layout": {
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
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
        Output("cases-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_cases_world_graph(selected_scale):
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.world[country]["date"],
                    "y": data.world[country]["total_cases_per_ten_thousand"],
                    "name": country,
                    "line": {
                        "width": 1.0,
                    }
                }
                for country in data.world
            ],
            "layout": {
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
                "legend": {
                    "x": 0.015,
                    "y": 1,
                    "traceorder": "normal",
                    "font": {"family": "sans-serif", "color": "white"},
                    "bgcolor": style.theme["background"],
                    "bordercolor": style.theme["accent"],
                    "borderwidth": 1,
                },
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.world[country]["date"],
                    "y": data.world[country]["total_deaths_per_ten_thousand"],
                    "name": country,
                    "line": {
                        "width": 1.0,
                    }
                }
                for country in data.world
            ],
            "layout": {
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_fatalities_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_fatalities_y"][lang].get(),
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass

try:
    @app.callback(
        Output("new-tests-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_tests_world_graph(selected_scale):
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.world[country]["date"],
                    "y": data.world[country]["new_tests_smoothed_per_ten_thousand"],
                    "name": country,
                    "line": {
                        "width": 1.0,
                    }
                }
                for country in data.world
            ],
            "layout": {
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_tests_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_tests_y"][lang].get(),
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }

except:
    pass


try:
    @app.callback(
        Output("test-positivity-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_test_positivity_world_graph(selected_scale):
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.world[country]["date"],
                    "y": data.world[country]["positive_rate"],
                    "name": country,
                    "mode": "lines",
                    "line": {
                        "width": 1.0,
                    }
                }
                for country in data.world
            ],
            "layout": {
                "height": 400,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_positivity_x"][lang].get(),
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_world_positivity_y"][lang].get(),
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }


except:
    pass


try:
    @app.callback(
        Output("tests-vs-positivity-world-graph", "figure"),
        [Input("radio-scale-switzerland", "value")],
    )
    def update_caseincrease_ch_graph(selected_scale):
        lang = get_lang()
        return {
            "data": [
                {
                    "x": data.world_no_na[country]["new_tests_smoothed_per_ten_thousand"].tail(7),
                    "y": data.world_no_na[country]["positive_rate"].tail(7) * 100,
                    "customdata": data.world_no_na[country]["date_label"].tail(7),
                    "name": country,
                    "mode": "lines",
                    "line": {
                        "width": 1.0,
                    },
                    "showlegend": False,
                    "hovertemplate": cfg["i18n"]["plot_tests_vs_positivity_hovertemplate"][lang].get(),
                }
                for country in data.world_no_na
            ] + [
                {
                    "x": data.world_no_na[country]["new_tests_smoothed_per_ten_thousand"].tail(1),
                    "y": data.world_no_na[country]["positive_rate"].tail(1) * 100,
                    "customdata": data.world_no_na[country]["date_label"].tail(1),
                    "name": country,
                    "text": country,
                    "mode": "markers+text",
                    "marker": {
                        "color": "white",
                    },
                    "showlegend": False,
                    "hovertemplate": cfg["i18n"]["plot_tests_vs_positivity_hovertemplate"][lang].get(),
                    "textposition": "top center",
                }
                for country in data.world_no_na
            ],
            "layout": {
                "height": 700,
                "xaxis": {
                    "showgrid": True,
                    "color": "#ffffff",
                    "title": cfg["i18n"]["plot_tests_vs_positivity_x"][lang].get(),
                    "type": selected_scale,
                },
                "yaxis": {
                    "type": selected_scale,
                    "showgrid": True,
                    "color": "#ffffff",
                    "rangemode": "tozero",
                    "title": cfg["i18n"]["plot_tests_vs_positivity_y"][lang].get(),
                },
                "hovermode": "closest",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
            },
        }
except:
    pass

# #
# # Age Distribution Data
# #
# try:

#     @app.callback(
#         Output("age-dist-cases-title", "children"),
#         [Input("radio-absolute-norm", "value")],
#     )
#     def updated_cases_bag_title(norm):
#         if norm == "scaled":
#             return cfg["i18n"]["plot_age_dist_scaled_title"][lang].get()
#         else:
#             return cfg["i18n"]["plot_age_dist_abs_title"][lang].get()

#     @app.callback(
#         Output("cases-bag-graph", "figure"),
#         [Input("select-regions-ch", "value"), Input("radio-absolute-norm", "value")],
#     )
#     def update_cases_bag_graph(region, norm):
#         lang = get_lang()
#         field = "cases"
#         factor = 1
#         ytitle = cfg["i18n"]["plot_age_dist_abs_y"][lang].get()

#         if norm == "scaled":
#             field = "cases_pp"
#             factor = 100
#             ytitle = cfg["i18n"]["plot_age_dist_scaled_y"][lang].get()

#         return {
#             "data": [
#                 {
#                     "x": data.age_data_male_hist[
#                         data.age_data_male_hist["region"] == region
#                     ]["age"],
#                     "y": data.age_data_male_hist[
#                         data.age_data_male_hist["region"] == region
#                     ][field]
#                     * factor,
#                     "name": cfg["i18n"]["male"][lang].get(),
#                     # "mode": "lines",
#                     "type": "bar",
#                     "line": {"width": 2.0, "color": "rgba(255, 5, 71, 1)",},
#                     "marker": {"color": "rgba(255, 5, 71, 0.5)"},
#                 },
#                 {
#                     "x": data.age_data_female_hist[
#                         data.age_data_female_hist["region"] == region
#                     ]["age"],
#                     "y": data.age_data_female_hist[
#                         data.age_data_female_hist["region"] == region
#                     ][field]
#                     * factor,
#                     "name": cfg["i18n"]["female"][lang].get(),
#                     # "mode": "lines",
#                     "type": "bar",
#                     "line": {"width": 2.0, "color": "rgba(56, 206, 255, 1)",},
#                     "marker": {"color": "rgba(56, 206, 255, 0.5)"},
#                 },
#             ],
#             "layout": {
#                 "height": 400,
#                 "xaxis": {
#                     "showgrid": True,
#                     "color": "#ffffff",
#                     "title": cfg["i18n"]["plot_age_dist_x"][lang].get(),
#                 },
#                 "yaxis": {
#                     "type": "linear",
#                     "showgrid": True,
#                     "color": "#ffffff",
#                     "rangemode": "tozero",
#                     "title": ytitle,
#                 },
#                 "legend": {
#                     "x": 0.015,
#                     "y": 1,
#                     "traceorder": "normal",
#                     "font": {"family": "sans-serif", "color": "white"},
#                     "bgcolor": style.theme["background"],
#                     "bordercolor": style.theme["accent"],
#                     "borderwidth": 1,
#                 },
#                 "barmode": "overlay",
#                 # "barmode": "stack",
#                 "bargap": 0,
#                 "dragmode": False,
#                 "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
#                 "plot_bgcolor": style.theme["background_secondary"],
#                 "paper_bgcolor": style.theme["background_secondary"],
#                 "font": {"color": style.theme["foreground_secondary"]},
#             },
#         }


# except:
#     pass

# try:
#     @app.callback(
#         Output("age-dist-fatalities-title", "children"),
#         [Input("radio-absolute-norm", "value")],
#     )
#     def updated_cases_bag_title(norm):
#         if norm == "scaled":
#             return cfg["i18n"]["plot_age_dist_fatalities_scaled_title"][lang].get()
#         else:
#             return cfg["i18n"]["plot_age_dist_fatalities_abs_title"][lang].get()

#     @app.callback(
#         Output("fatalities-bag-graph", "figure"),
#         [Input("select-regions-ch", "value"), Input("radio-absolute-norm", "value")],
#     )
#     def update_fatalities_bag_graph(region, norm):
#         lang = get_lang()
#         field = "fatalities"
#         factor = 1
#         ytitle = cfg["i18n"]["plot_age_dist_fatalities_abs_y"][lang].get()

#         if norm == "scaled":
#             field = "fatalities_pp"
#             factor = 100
#             ytitle = cfg["i18n"]["plot_age_dist_fatalities_scaled_y"][lang].get()

#         return {
#             "data": [
#                 {
#                     "x": data.age_data_male_hist[
#                         data.age_data_male_hist["region"] == region
#                     ]["age"],
#                     "y": data.age_data_male_hist[
#                         data.age_data_male_hist["region"] == region
#                     ][field]
#                     * factor,
#                     "name": cfg["i18n"]["male"][lang].get(),
#                     # "mode": "lines",
#                     "type": "bar",
#                     "line": {"width": 2.0, "color": "rgba(255, 5, 71, 1)",},
#                     "marker": {"color": "rgba(255, 5, 71, 0.5)"},
#                 },
#                 {
#                     "x": data.age_data_female_hist[
#                         data.age_data_female_hist["region"] == region
#                     ]["age"],
#                     "y": data.age_data_female_hist[
#                         data.age_data_female_hist["region"] == region
#                     ][field]
#                     * factor,
#                     "name": cfg["i18n"]["female"][lang].get(),
#                     # "mode": "lines",
#                     "type": "bar",
#                     "line": {"width": 2.0, "color": "rgba(56, 206, 255, 1)",},
#                     "marker": {"color": "rgba(56, 206, 255, 0.5)"},
#                 },
#             ],
#             "layout": {
#                 "height": 400,
#                 "xaxis": {
#                     "showgrid": True,
#                     "color": "#ffffff",
#                     "title": cfg["i18n"]["plot_age_dist_fatalities_x"][lang].get(),
#                 },
#                 "yaxis": {
#                     "type": "linear",
#                     "showgrid": True,
#                     "color": "#ffffff",
#                     "rangemode": "tozero",
#                     "title": ytitle,
#                 },
#                 "legend": {
#                     "x": 0.015,
#                     "y": 1,
#                     "traceorder": "normal",
#                     "font": {"family": "sans-serif", "color": "white"},
#                     "bgcolor": style.theme["background"],
#                     "bordercolor": style.theme["accent"],
#                     "borderwidth": 1,
#                 },
#                 "barmode": "overlay",
#                 # "barmode": "stack",
#                 "bargap": 0,
#                 "dragmode": False,
#                 "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
#                 "plot_bgcolor": style.theme["background_secondary"],
#                 "paper_bgcolor": style.theme["background_secondary"],
#                 "font": {"color": style.theme["foreground_secondary"]},
#             },
#         }

# except:
#     pass

try:
    @app.callback(
        Output("region-boxes", "figure"),
        [Input("dropdown-regions", "value"), Input("radio-scale-regions", "value")],
    )
    def update_region_boxes(selected_regions, selected_scale):
        lang = get_lang()
        d = data.swiss_cases_by_date_diff
        d_selected = d[selected_regions] / data.swiss_cases_updated_mask_by_date[selected_regions]
        
        region_order = d_selected.transpose().sum(axis=1).sort_values().transpose().index
        
        d_selected = d_selected[region_order]
        values = d_selected.values.transpose()
        
        return {
            "data": [
                {
                    "x": d.index,
                    "y": list(d_selected.columns),
                    "z": values,
                    "customdata": d_selected.replace(np.nan, cfg["i18n"]["plot_regional_null"][lang].get(), regex=True).values.transpose(),
                    "colorscale": "Portland",
                    "hovertemplate": "<br><span style='font-size:2.0em'><b>%{customdata}</b></span><b> %{y}</b><br>%{x}<extra></extra>",
                    "type": "heatmap",
                }
            ],
            "layout": {
                "height": 500,
                "xaxis": {
                    "showgrid": False,
                    "title": cfg["i18n"]["plot_regional_overview_x"][lang].get(),
                },
                "yaxis": {
                    "showgrid": False,
                    "title": cfg["i18n"]["plot_regional_overview_y"][lang].get(),
                },
                # "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 80},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                # "shapes": phase_shapes,
                # "annotations": phase_annotations_double_height,
            },
        }
except:
    pass

#
# Regional Data
#
try:

    @app.callback(
        Output("case-graph", "figure"),
        [Input("dropdown-regions", "value"), Input("radio-scale-regions", "value")],
    )
    def update_case_graph(selected_regions, selected_scale):
        lang = get_lang()
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
                "hovermode": "x unified",
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
        lang = get_lang()
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
                "hovermode": "x unified",
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
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
        lang = get_lang()
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
                "hovermode": "x unified",
                "dragmode": False,
                "margin": {"l": 60, "r": 10, "t": 30, "b": 70},
                "plot_bgcolor": style.theme["background"],
                "paper_bgcolor": style.theme["background"],
                "font": {"color": style.theme["foreground"]},
                "barmode": "stack",
                "shapes": phase_shapes,
                "annotations": phase_annotations_double_height,
            },
        }


except:
    pass

#
# Map (client-side)
#

try:
    app.clientside_callback(
        ClientsideFunction(
            namespace="clientside", function_name="update_map"
        ),
        Output("update-map", "figure"),
        [
            Input("map-radios", "value"),
            Input("slider-date", "value"),
            Input("map-data", "children"),
        ],
    )
except:
    pass

try:

    @app.callback(
        Output("map-data", "children"), [Input("url", "pathname")]
    )
    def store_map_data(value):
        settings = {
            "total_column_name": cfg["settings"]["total_column_name"].get(),
            "choropleth": {
                "geojson_file": cfg["settings"]["choropleth"]["geojson_file"].get(),
                "feature": cfg["settings"]["choropleth"]["feature"].get(),
                "center": cfg["settings"]["choropleth"]["center"].get(),
                "lataxis": cfg["settings"]["choropleth"]["lataxis"].get(),
                "lonaxis": cfg["settings"]["choropleth"]["lonaxis"].get(),
            }
        }

        theme = {
            "background": cfg["theme"]["background"].get()
        }

        return (
            '{"swiss_cases": '
            + data.swiss_cases.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_cases_by_date_filled": '
            + data.swiss_cases_by_date_filled.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_cases_by_date_filled_per_capita": '
            + data.swiss_cases_by_date_filled_per_capita.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_fatalities_by_date_filled": '
            + data.swiss_fatalities_by_date_filled.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_cases_by_date_diff": '
            + data.swiss_cases_by_date_diff.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_fatalities_by_date_diff": '
            + data.swiss_fatalities_by_date_diff.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_hospitalizations_by_date_diff": '
            + data.swiss_hospitalizations_by_date_diff.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_hospitalizations_by_date_filled": '
            + data.swiss_hospitalizations_by_date_filled.to_json(
                date_format="iso", orient="columns"
            )
            + ', "swiss_cases_updated_mask_by_date": '
            + data.swiss_cases_updated_mask_by_date.to_json(
                date_format="iso", orient="columns"
            )
            + ', "regional_centres": '
            + json.dumps(data.regional_centres)
            + ', "settings": '
            + json.dumps(settings)
            + ', "theme":'
            + json.dumps(theme)
            + ', "turbo":'
            + json.dumps(style.turbo)
            + ', "region_labels":'
            + json.dumps(data.region_labels)
            + ', "region_updates":'
            + json.dumps(data.last_updated["Updated_Today"].to_dict())
            + '}'
        )
except:
    pass

#
# Regional log-log graph (client-based)
#

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
        lang = get_lang()
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
