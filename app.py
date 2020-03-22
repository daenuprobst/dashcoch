# -*- coding: utf-8 -*-
import math
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


#
# Get the data
#
url = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland.csv"
df = pd.read_csv(url, error_bad_lines=False)

url_fatalities = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_fatalities_switzerland.csv"
df_fatalities = pd.read_csv(url_fatalities, error_bad_lines=False)

url_pred = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/predicted.csv"
df_pred = pd.read_csv(url_pred, error_bad_lines=False)

url_demo = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/demographics.csv"
df_demo = pd.read_csv(url_demo, error_bad_lines=False, index_col=0)

df_map = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/2011_february_us_airport_traffic.csv"
)

url_world = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv"
df_world = pd.read_csv(url_world)

url_world_fatalities = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv"
df_world_fatalities = pd.read_csv(url_world_fatalities)

#
# Load boundaries for the cantons
#
canton_boundaries = geojson.load(open("assets/switzerland.geojson", "r"))

#
# Centres of cantons
#
centres_cantons = {
    "AG": {"lat": 47.40966, "lon": 8.15688},
    "AR": {"lat": 47.366352 + 0.05, "lon": 9.36791},
    "AI": {"lat": 47.317264, "lon": 9.416754},
    "BL": {"lat": 47.45176, "lon": 7.702414},
    "BS": {"lat": 47.564869, "lon": 7.615259},
    "BE": {"lat": 46.823608, "lon": 7.636667},
    "FR": {"lat": 46.718391, "lon": 7.074008},
    "GE": {"lat": 46.220528, "lon": 6.132935},
    "GL": {"lat": 46.981042 - 0.05, "lon": 9.065751},
    "GR": {"lat": 46.656248, "lon": 9.628198},
    "JU": {"lat": 47.350744, "lon": 7.156107},
    "LU": {"lat": 47.067763, "lon": 8.1102},
    "NE": {"lat": 46.995534, "lon": 6.780126},
    "NW": {"lat": 46.926755, "lon": 8.405302},
    "OW": {"lat": 46.854527 - 0.05, "lon": 8.244317 - 0.1},
    "SH": {"lat": 47.71357, "lon": 8.59167},
    "SZ": {"lat": 47.061787, "lon": 8.756585},
    "SO": {"lat": 47.304135, "lon": 7.639388},
    "SG": {"lat": 47.2332 - 0.05, "lon": 9.274744},
    "TI": {"lat": 46.295617, "lon": 8.808924},
    "TG": {"lat": 47.568715, "lon": 9.091957},
    "UR": {"lat": 46.771849, "lon": 8.628586},
    "VD": {"lat": 46.570091, "lon": 6.657809 - 0.1},
    "VS": {"lat": 46.209567, "lon": 7.604659},
    "ZG": {"lat": 47.157296, "lon": 8.537294},
    "ZH": {"lat": 47.41275, "lon": 8.65508},
}

#
# Wrangle the data
#
df_by_date = df.set_index("Date")
df_fatalities_by_date = df_fatalities.set_index("Date")
latest_date = df.iloc[len(df) - 1]["Date"]

# Get the cantons that were updated today to display below the map
cantons_updated_today = [
    canton
    for canton in df_by_date.iloc[len(df_by_date) - 1][
        df_by_date.iloc[len(df_by_date) - 1].notnull()
    ].index
]

cases_new = (
    df_by_date.diff().iloc[len(df_by_date) - 1].sum()
    - df_by_date.diff().iloc[len(df_by_date) - 1]["CH"]
)

# If a new day starts and there is no info yet, show no new cases
if date.fromisoformat(latest_date) != datetime.now(timezone("Europe/Zurich")).date():
    cases_new = 0

# Fill all the missing data by previously reported data
df_by_date = df_by_date.fillna(method="ffill", axis=0)
df_by_date_pc = df_by_date.copy()
for column in df_by_date_pc:
    df_by_date_pc[column] = (
        df_by_date_pc[column] / df_demo["Population"][column] * 10000
    )

cases_total = (
    df_by_date.iloc[len(df_by_date) - 1].sum()
    - df_by_date.iloc[len(df_by_date) - 1]["CH"]
)

fatalities_total = (
    df_fatalities_by_date.iloc[len(df_fatalities_by_date) - 1].sum()
    - df_fatalities_by_date.iloc[len(df_fatalities_by_date) - 1]["CH"]
)


# Get the data in list form and normalize it
data = df.to_dict("list")
canton_labels = [canton for canton in data if canton != "CH" and canton != "Date"]
data_norm = {
    str(canton): [
        round(i, 2) for i in data[canton] / df_demo["Population"][canton] * 10000
    ]
    for canton in data
    if canton != "Date"
}
data_norm["Date"] = data["Date"]

#
# World data
#
df_world.drop(columns=["Lat", "Long"], inplace=True)
df_world["Province/State"].fillna("", inplace=True)
df_world = df_world.rename(columns={"Country/Region": "Day"})
df_world = df_world.groupby("Day").sum()
df_world = df_world.T
df_world.drop(
    df_world.columns.difference(
        ["France", "Germany", "Italy", "Spain", "United Kingdom", "US"]
    ),
    1,
    inplace=True,
)

df_world.index = range(0, len(df_world))

# Shift the data to the start (remove leading zeros in columns)
df_world["Switzerland"] = pd.Series(data["CH"])
pop_world = {
    "France": 65273511,
    "Germany": 83783942,
    "Italy": 60461826,
    "Spain": 46754778,
    "US": 331002651,
    "United Kingdom": 67886011,
    "Switzerland": 8654622,
}

for column in df_world:
    df_world[column] = df_world[column] / pop_world[column] * 10000

df_world[df_world < 0.4] = 0
for column in df_world:
    while df_world[column].iloc[0] == 0:
        df_world[column] = df_world[column].shift(-1)
df_world.dropna(how="all", inplace=True)

#
# The predicted data
#
data_pred = df_pred.to_dict("list")
data_pred_norm = {
    str(canton): [
        round(i, 2) for i in data_pred[canton] / df_demo["Population"][canton] * 10000
    ]
    for canton in data_pred
    if canton != "Date"
}
data_pred_norm["Date"] = data_pred["Date"]

#
# Some nice differentiable colors for the cantons + CH
#
colors = [
    "#7a8871",
    "#a359e3",
    "#91e63f",
    "#dd47ba",
    "#5ad358",
    "#6e7edc",
    "#d9dd3d",
    "#c376bc",
    "#a8cc5f",
    "#d95479",
    "#63de9f",
    "#de4f37",
    "#74deda",
    "#dd892d",
    "#71adcf",
    "#dbbd59",
    "#797ca6",
    "#4e9648",
    "#d4b7d8",
    "#8a873d",
    "#489889",
    "#b1743d",
    "#a8d5a2",
    "#a87575",
    "#d6cead",
    "#e59780",
    "#000000",
]

color_scale = [
    "#f2fffb",
    "#bbffeb",
    "#98ffe0",
    "#79ffd6",
    "#6df0c8",
    "#69e7c0",
    "#59dab2",
    "#45d0a5",
    "#31c194",
    "#2bb489",
    "#25a27b",
    "#1e906d",
    "#188463",
    "#157658",
    "#11684d",
    "#10523e",
]

theme = {"background": "#252e3f", "foreground": "#2cfec1", "accent": "#7fafdf"}

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
                                    children=str(int(cases_total)),
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
                                    children="+" + str(int(cases_new)),
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
                                    children=str(int(fatalities_total)),
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
                    max=len(df["Date"]) - 1,
                    marks={
                        i: date.fromisoformat(d).strftime("%d. %m.")
                        for i, d in enumerate(df["Date"])
                    },
                    value=len(df["Date"]) - 1,
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
                        "color": theme["foreground"],
                    },
                ),
            ],
        ),
        html.Div(children=[dcc.Graph(id="graph-map", config={"staticPlot": True},),]),
        html.Div(
            children=[
                "Cantons updated today: ",
                html.Span(", ".join(cantons_updated_today)),
            ]
        ),
        html.Br(),
        html.H4(children="Data for Switzerland", style={"color": theme["accent"]}),
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
        # html.Div(
        #     className="row",
        #     children=[
        #         html.Div(
        #             className="six columns",
        #             children=[dcc.Graph(id="fatalities-ch-graph")],
        #         ),
        #         html.Div(
        #             className="six columns",
        #             children=[dcc.Graph(id="fatalities-world-graph")],
        #         ),
        #     ],
        # ),
        html.Br(),
        html.H4(children="Data per Canton", style={"color": theme["accent"]}),
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
                        "color": theme["foreground"],
                    },
                ),
                html.Br(),
                dcc.Dropdown(
                    id="dropdown-cantons",
                    options=[
                        {"label": canton, "value": canton} for canton in canton_labels
                    ],
                    value=canton_labels,
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
        # html.H4(
        #     children="Interpolated and Predicted Data", style={"color": theme["accent"]}
        # ),
        # html.Div(
        #     className="row",
        #     children=[
        #         html.Div(
        #             className="six columns", children=[dcc.Graph(id="case-graph-pred")]
        #         ),
        #         html.Div(
        #             className="six columns",
        #             children=[dcc.Graph(id="case-pc-graph-pred"),],
        #         ),
        #     ],
        # ),
        html.H4(children="Raw Data", style={"color": theme["accent"]}),
        dash_table.DataTable(
            id="table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
        ),
        html.H4(children="Raw Data (Predicted)", style={"color": theme["accent"]}),
        dash_table.DataTable(
            id="table_pred",
            columns=[{"name": i, "id": i} for i in df_pred.columns],
            data=df_pred.to_dict("records"),
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
    date = df["Date"].iloc[selected_date_index]

    map_data = df_by_date
    labels = [
        canton + ": " + str(int(map_data[canton][date])) for canton in centres_cantons
    ]

    if mode == "prevalence":
        map_data = df_by_date_pc
        labels = [
            canton + ": " + str(round((map_data[canton][date]), 1))
            for canton in centres_cantons
        ]
    elif mode == "fatalities":
        map_data = df_fatalities_by_date
        labels = [
            canton + ": " + str(int(map_data[canton][date]))
            if not math.isnan(float(map_data[canton][date]))
            else ""
            for canton in centres_cantons
        ]

    return {
        "data": [
            {
                "lat": [centres_cantons[canton]["lat"] for canton in centres_cantons],
                "lon": [centres_cantons[canton]["lon"] for canton in centres_cantons],
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
                "locations": canton_labels,
                "z": [map_data[canton][date] for canton in map_data if canton != "CH"],
                "colorscale": [(0, "#7F2238"), (1, "#FF3867")],
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
                "fitbounds": "locations",
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
                "x": data["Date"],
                "y": data["CH"],
                "name": "CH",
                "marker": {"color": theme["foreground"]},
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
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


# @app.callback(
#     Output("fatalities-ch-graph", "figure"), [Input("radio-scale", "value")],
# )
# def update_fatalities_ch_graph(selected_scale):
#     return {
#         "data": [
#             {
#                 "x": df_fatalities["Date"],
#                 "y": df_fatalities["CH"],
#                 "name": "CH",
#                 "marker": {"color": theme["foreground"]},
#                 "type": "bar",
#             }
#         ],
#         "layout": {
#             "title": "Total Fatalities Switzerland",
#             "height": 400,
#             "xaxis": {"showgrid": True, "color": "#ffffff"},
#             "yaxis": {
#                 "type": selected_scale,
#                 "showgrid": True,
#                 "color": "#ffffff",
#                 "rangemode": "tozero",
#             },
#             "plot_bgcolor": theme["background"],
#             "paper_bgcolor": theme["background"],
#             "font": {"color": theme["foreground"]},
#         },
#     }


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
                "x": df_world.index.values,
                "y": df_world[country],
                "name": country,
                # "marker": {"color": theme["foreground"]},
                # "type": "bar",
            }
            for country in df_world
            if country != "Day"
        ],
        "layout": {
            "title": "Prelavence per 10,000 Inhabitants",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Days Since Prevalence >0.4 per 10,000",
            },
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff",},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
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
                "x": data["Date"],
                "y": data[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Cases per Canton",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
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
                "x": data_norm["Date"],
                "y": data_norm[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Cases per Canton (per 10,000 Inhabitants)",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


@app.callback(
    Output("case-graph-diff", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_graph_diff(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data["Date"],
                "y": [0] + [j - i for i, j in zip(data[canton][:-1], data[canton][1:])],
                "name": canton,
                "marker": {"color": colors[i - 1]},
                "type": "bar",
            }
            for i, canton in enumerate(data)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "New Cases per Canton",
            "height": 750,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
            "barmode": "stack",
        },
    }


# #
# # Predictions: cases per canton
# #
# @app.callback(
#     Output("case-graph-pred", "figure"),
#     [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
# )
# def update_case_graph_pred(selected_cantons, selected_scale):
#     return {
#         "data": [
#             {
#                 "x": data_pred["Date"],
#                 "y": data_pred[canton],
#                 "name": canton,
#                 "marker": {"color": colors[i - 1]},
#             }
#             for i, canton in enumerate(data_pred)
#             if canton in selected_cantons
#         ],
#         "layout": {
#             "title": "Cases per Canton",
#             "height": 750,
#             "xaxis": {"showgrid": True, "color": "#ffffff"},
#             "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
#             "plot_bgcolor": theme["background"],
#             "paper_bgcolor": theme["background"],
#             "font": {"color": theme["foreground"]},
#         },
#     }


# #
# # Predictions: cases per canton (per 10'000 inhabitants)
# #
# @app.callback(
#     Output("case-pc-graph-pred", "figure"),
#     [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
# )
# def update_case_pc_graph_pred(selected_cantons, selected_scale):
#     return {
#         "data": [
#             {
#                 "x": data_pred_norm["Date"],
#                 "y": data_pred_norm[canton],
#                 "name": canton,
#                 "marker": {"color": colors[i - 1]},
#             }
#             for i, canton in enumerate(data_pred)
#             if canton in selected_cantons
#         ],
#         "layout": {
#             "title": "Cases per Canton (per 10,000 Inhabitants)",
#             "height": 750,
#             "xaxis": {"showgrid": True, "color": "#ffffff"},
#             "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},
#             "plot_bgcolor": theme["background"],
#             "paper_bgcolor": theme["background"],
#             "font": {"color": theme["foreground"]},
#         },
#    }


if __name__ == "__main__":
    app.run_server(
        # debug=True,
        # dev_tools_hot_reload=True,
        # dev_tools_hot_reload_interval=50,
        # dev_tools_hot_reload_max_retry=30,
    )
