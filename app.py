# -*- coding: utf-8 -*-
import i18n
from dashcoch import DataLoader, StyleLoader
import math
from configparser import ConfigParser
from datetime import date, datetime
from pytz import timezone
import geojson
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
parser = ConfigParser()
parser.read("settings.ini")

data = DataLoader(parser)
style = StyleLoader()


#
# General app settings
#
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Swiss COVID19 Tracker"

#
# Show the data
#
app.layout = html.Div(
    id="main",
    children=[
        html.Div(
            id="header",
            children=[
                html.H4(children="COVID-19 Cases Switzerland"),
                html.P(
                    id="description",
                    children=[
                        dcc.Markdown(
                            """
                            **All data shown on this website was collected from the cantonal data published on the cantonal websites**
                        Number of COVID-19 cases in Switzerland. Data compiled and visualised by [@sketpeis](https://twitter.com/skepteis). 
                        Please direct any criticism or ideas to me.
                        The data source can be found [here](https://github.com/daenuprobst/covid19-cases-switzerland).
                        """
                        )
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="twelve columns",
                    children=[
                        html.Div(
                            className="total-container",
                            children=[
                                html.P(className="total-title", children="Total Cases"),
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
                                    className="total-title", children="New Cases Today"
                                ),
                                html.Div(
                                    className="total-content",
                                    children="+" + str(int(data.new_swiss_cases)),
                                ),
                            ],
                        ),
                        html.Div(
                            className="total-container",
                            children=[
                                html.P(
                                    className="total-title", children="Total Fatalities"
                                ),
                                html.Div(
                                    className="total-content",
                                    children=str(int(data.total_swiss_fatalities)),
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(className="six columns"),
                html.Div(className="six columns"),
            ],
        ),
        html.Br(),
        html.Div(
            id="slider-container",
            children=[
                html.P(
                    id="slider-text", children="Drag the slider to change the date:",
                ),
                dcc.Slider(
                    id="slider-date",
                    min=0,
                    max=len(data.swiss_cases["Date"]) - 1,
                    marks={
                        i: date.fromisoformat(d).strftime("%d. %m.")
                        for i, d in enumerate(data.swiss_cases["Date"])
                    },
                    value=len(data.swiss_cases["Date"]) - 1,
                ),
                html.Br(),
                dcc.RadioItems(
                    id="radio-prevalence",
                    options=[
                        {"label": "Number of Cases", "value": "number"},
                        {"label": "Prevalence (per 10,000)", "value": "prevalence"},
                        {"label": "Number of Fatalities", "value": "fatalities"},
                    ],
                    value="number",
                    labelStyle={
                        "display": "inline-block",
                        "color": style.theme["foreground"],
                    },
                ),
            ],
        ),
        html.Div(children=[dcc.Graph(id="graph-map", config={"staticPlot": True},),]),
        html.Div(
            children=[
                "Cantons updated today: ",
                html.Span(", ".join(data.updated_cantons)),
            ]
        ),
        html.Br(),
        html.H4(
            children="Data for Switzerland", style={"color": style.theme["accent"]}
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-ch-graph")]
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="case-world-graph")],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="fatalities-ch-graph")],
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="fatalities-world-graph")],
                ),
            ],
        ),
        html.Br(),
        html.H4(children="Data per Canton", style={"color": style.theme["accent"]}),
        html.Div(
            id="plot-settings-container",
            children=[
                html.P(
                    id="plot-settings-text",
                    children="Select scale and cantons to show in the plots:",
                ),
                dcc.RadioItems(
                    id="radio-scale",
                    options=[
                        {"label": "Linear Scale", "value": "linear"},
                        {"label": "Logarithmic Scale", "value": "log"},
                    ],
                    value="linear",
                    labelStyle={
                        "display": "inline-block",
                        "color": style.theme["foreground"],
                    },
                ),
                html.Br(),
                dcc.Dropdown(
                    id="dropdown-cantons",
                    options=[
                        {"label": canton, "value": canton}
                        for canton in data.canton_labels
                    ],
                    value=data.canton_labels,
                    multi=True,
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-graph")]
                ),
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-pc-graph"),],
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
        html.H4(children="Raw Data", style={"color": style.theme["accent"]}),
        dash_table.DataTable(
            id="table",
            columns=[{"name": i, "id": i} for i in data.swiss_cases.columns],
            data=data.swiss_cases.to_dict("records"),
        ),
    ],
)

# -------------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------------
@app.callback(
    Output("graph-map", "figure"),
    [Input("slider-date", "value"), Input("radio-prevalence", "value")],
)
def update_graph_map(selected_date_index, mode):
    date = data.swiss_cases["Date"].iloc[selected_date_index]

    map_data = data.swiss_cases_by_date_filled
    labels = [
        canton + ": " + str(int(map_data[canton][date]))
        for canton in data.cantonal_centres
    ]

    if mode == "prevalence":
        map_data = data.swiss_cases_by_date_filled_per_capita
        labels = [
            canton + ": " + str(round((map_data[canton][date]), 1))
            for canton in data.cantonal_centres
        ]
    elif mode == "fatalities":
        map_data = data.swiss_fatalities_by_date
        labels = [
            canton + ": " + str(int(map_data[canton][date]))
            if not math.isnan(float(map_data[canton][date]))
            else ""
            for canton in data.cantonal_centres
        ]

    return {
        "data": [
            {
                "lat": [
                    data.cantonal_centres[canton]["lat"]
                    for canton in data.cantonal_centres
                ],
                "lon": [
                    data.cantonal_centres[canton]["lon"]
                    for canton in data.cantonal_centres
                ],
                "text": labels,
                "mode": "text",
                "type": "scattergeo",
                "textfont": {
                    "family": "sans serif",
                    "size": 18,
                    "color": "white",
                    "weight": "bold",
                },
            },
            {
                "type": "choropleth",
                "locations": data.canton_labels,
                "z": [map_data[canton][date] for canton in map_data if canton != "CH"],
                "colorscale": style.turbo,
                "geojson": "/assets/switzerland.geojson",
                "marker": {"line": {"width": 0.0, "color": "#08302A"}},
                "colorbar": {
                    "thickness": 10,
                    "bgcolor": "#252e3f",
                    "tickfont": {"color": "white"},
                },
            },
        ],
        "layout": {
            "geo": {
                "visible": False,
                "center": {"lat": 46.80111, "lon": 8.22667},
                "lataxis": {"range": [45.7845, 47.8406]},
                "lonaxis": {"range": [5.5223, 10.5421]},
                # "fitbounds": "geojson",
                "projection": {"type": "transverse mercator"},
                # "landcolor": "#1f2630",
                # "showland": True,
                # "showcountries": True,
            },
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "height": 600,
            "plot_bgcolor": "#252e3f",
            "paper_bgcolor": "#252e3f",
        }
        # "layout": {
        #     "mapbox": {
        #         "accesstoken": "pk.eyJ1IjoiZGFlbnVwcm9ic3QiLCJhIjoiY2s3eDR2dmRyMDg0ajN0cDlkaDNmM3J0NyJ9.tcJPFQkbsVGlWpyQaKPtiw",
        #         "style": "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz",
        #         "center": {"lat": 46.8181877, "lon": 8.2275124},
        #         "pitch": 0,
        #         "zoom": 7,
        #     },
        #     "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
        #     "height": 600,
        #     "plot_bgcolor": "#1f2630",
        #     "paper_bgcolor": "#1f2630",
        # },
    }


#
# Total cases Switzerland
#
@app.callback(
    Output("case-ch-graph", "figure"), [Input("radio-scale", "value")],
)
def update_case_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases_as_dict["Date"],
                "y": data.swiss_cases_as_dict["CH"],
                "name": "CH",
                "marker": {"color": style.theme["foreground"]},
                "type": "bar",
            }
        ],
        "layout": {
            "title": "Total Cases Switzerland",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
            },
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("fatalities-ch-graph", "figure"), [Input("radio-scale", "value")],
)
def update_fatalities_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_fatalities["Date"],
                "y": data.swiss_fatalities["CH"],
                "name": "CH",
                "marker": {"color": style.theme["foreground"]},
                "type": "bar",
            }
        ],
        "layout": {
            "title": "Total Fatalities Switzerland",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
            },
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


#
# Total cases world
#
@app.callback(
    Output("case-world-graph", "figure"), [Input("radio-scale", "value")],
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
            "title": "Prevalence per 10,000 Inhabitants",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Days Since Prevalence >0.4 per 10,000",
            },
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff",},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("fatalities-world-graph", "figure"), [Input("radio-scale", "value")],
)
def update_fatalities_world_graph(selected_scale):
    return {
        "data": [
            {
                "x": ["Switzerland"]
                + data.world_case_fatality_rate.index.values.tolist(),
                "y": [data.swiss_case_fatality_rate]
                + [val for val in data.world_case_fatality_rate],
                "name": "CH",
                "marker": {"color": style.theme["foreground"]},
                "type": "bar",
            }
        ],
        "layout": {
            "title": "Case Fatality Rates (Fatalities / Cases)",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
            },
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


#
# Cantonal Data
#
@app.callback(
    Output("case-graph", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_graph(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases_as_dict["Date"],
                "y": data.swiss_cases_as_dict[canton],
                "name": canton,
                "marker": {"color": style.colors[i - 1]},
            }
            for i, canton in enumerate(data.swiss_cases_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Cases per Canton",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("case-pc-graph", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_pc_graph(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases_normalized_as_dict["Date"],
                "y": data.swiss_cases_normalized_as_dict[canton],
                "name": canton,
                "marker": {"color": style.colors[i - 1]},
            }
            for i, canton in enumerate(data.swiss_cases_normalized_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Cases per Canton (per 10,000 Inhabitants)",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("case-graph-diff", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_graph_diff(selected_cantons, selected_scale):
    data_non_nan = {}
    data_non_nan["Date"] = data.swiss_cases_as_dict["Date"]

    for canton in data.swiss_cases_as_dict:
        if canton == "Date":
            continue
        values = []
        last_value = 0
        for _, v in enumerate(data.swiss_cases_as_dict[canton]):
            if math.isnan(float(v)):
                values.append(last_value)
            else:
                last_value = v
                values.append(v)
        data_non_nan[canton] = values

    return {
        "data": [
            {
                "x": data_non_nan["Date"],
                "y": [0]
                + [
                    j - i
                    for i, j in zip(data_non_nan[canton][:-1], data_non_nan[canton][1:])
                ],
                "name": canton,
                "marker": {"color": style.colors[i - 1]},
                "type": "bar",
            }
            for i, canton in enumerate(data.swiss_cases_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "New Cases per Canton",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
            "barmode": "stack",
        },
    }


if __name__ == "__main__":
    app.run_server(
        # debug=True,
        # dev_tools_hot_reload=True,
        # dev_tools_hot_reload_interval=50,
        # dev_tools_hot_reload_max_retry=30,
    )
