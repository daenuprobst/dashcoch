# -*- coding: utf-8 -*-
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

# Get the data
url = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland.csv"
df = pd.read_csv(url, error_bad_lines=False)

url_pred = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/predicted.csv"
df_pred = pd.read_csv(url_pred, error_bad_lines=False)

url_demo = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/demographics.csv"
df_demo = pd.read_csv(url_demo, error_bad_lines=False, index_col=0)

df_map = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/2011_february_us_airport_traffic.csv"
)

# Centres of cantons
centres_cantons = {
    "AG": {"lat": 47.40966, "lon": 8.15688},
    "AR": {"lat": 47.366352, "lon": 9.36791},
    "AI": {"lat": 47.317264, "lon": 9.416754},
    "BL": {"lat": 47.45176, "lon": 7.702414},
    "BS": {"lat": 47.564869, "lon": 7.615259},
    "BE": {"lat": 46.823608, "lon": 7.636667},
    "FR": {"lat": 46.718391, "lon": 7.074008},
    "GE": {"lat": 46.220528, "lon": 6.132935},
    "GL": {"lat": 46.981042, "lon": 9.065751},
    "GR": {"lat": 46.656248, "lon": 9.628198},
    "JU": {"lat": 47.350744, "lon": 7.156107},
    "LU": {"lat": 47.067763, "lon": 8.1102},
    "NE": {"lat": 46.995534, "lon": 6.780126},
    "NW": {"lat": 46.926755, "lon": 8.405302},
    "OW": {"lat": 46.854527, "lon": 8.244317},
    "SH": {"lat": 47.71357, "lon": 8.59167},
    "SZ": {"lat": 47.061787, "lon": 8.756585},
    "SO": {"lat": 47.304135, "lon": 7.639388},
    "SG": {"lat": 47.2332, "lon": 9.274744},
    "TI": {"lat": 46.295617, "lon": 8.808924},
    "TG": {"lat": 47.568715, "lon": 9.091957},
    "UR": {"lat": 46.771849, "lon": 8.628586},
    "VD": {"lat": 46.570091, "lon": 6.657809},
    "VS": {"lat": 46.209567, "lon": 7.604659},
    "ZG": {"lat": 47.157296, "lon": 8.537294},
    "ZH": {"lat": 47.41275, "lon": 8.65508},
}

# Wrangle the data
df_by_date = df.set_index("Date")
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

# The predicted data
data_pred = df_pred.to_dict("list")
data_pred_norm = {
    str(canton): [
        round(i, 2) for i in data_pred[canton] / df_demo["Population"][canton] * 10000
    ]
    for canton in data_pred
    if canton != "Date"
}
data_pred_norm["Date"] = data_pred["Date"]

# Some nice differentiable colors for the cantons + CH
colors = [
    "#4bafd5",
    "#d65723",
    "#8a61d5",
    "#69aa31",
    "#d04dac",
    "#55c160",
    "#dc3d6f",
    "#58c39a",
    "#cd473d",
    "#308b75",
    "#88529e",
    "#b0ba3b",
    "#637fcb",
    "#db9c30",
    "#d18dd2",
    "#3b7f3c",
    "#a64b76",
    "#a6ba70",
    "#ab4a51",
    "#769550",
    "#e4828e",
    "#8c8426",
    "#e18a5f",
    "#626524",
    "#c7a05c",
    "#995d2a",
    "#000000",
]

theme = {"background": "#252e3f", "foreground": "#2cfec1", "accent": "#7fafdf"}


# General app settings
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Swiss COVID19 Tracker"

# Show the data
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
            id="slider-container",
            children=[
                html.P(
                    id="slider-text", children="Drag the slider to change the date:",
                ),
                dcc.Slider(
                    id="slider-date",
                    min=0,
                    max=len(df["Date"]) - 1,
                    marks={i: d for i, d in enumerate(df["Date"])},
                    value=len(df["Date"]) - 1,
                ),
            ],
        ),
        html.Div(children=[dcc.Graph(id="graph-map", config={"staticPlot": True},),]),
        html.Br(),
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
        html.H4(
            children="Data for Switzerland", style={"color": theme["accent"]}
        ),        
        html.Div(
            className="row",
            children=[        
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-ch-graph")]
                ),
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-ch-graph-pred")]
                ),
            ],
        ),
        html.Br(),
        html.H4(
            children="Data per Canton", style={"color": theme["accent"]}
        ),
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
        html.H4(
            children="Interpolated and Predicted Data", style={"color": theme["accent"]}
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-graph-pred")]
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="case-pc-graph-pred"),],
                ),
            ],
        ),
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
    Output("graph-map", "figure"), [Input("slider-date", "value")],
)
def update_graph_map(selected_date_index):
    date = df["Date"].iloc[selected_date_index]

    return {
        "data": [
            {
                "lat": [centres_cantons[canton]["lat"] for canton in centres_cantons],
                "lon": [centres_cantons[canton]["lon"] for canton in centres_cantons],
                "text": [
                    # I know, I know it's hacky, but checking for nans is always ugly in Python and I can't be
                    # bothered to import numpy just for this
                    n.replace(".0", "").replace("nan", "?")
                    for n in [
                        canton + ": " + str(df_by_date[canton][date])
                        for canton in centres_cantons
                    ]
                ],
                "mode": "text",
                "type": "scattermapbox",
                "textfont": {
                    "family": "sans serif",
                    "size": 18,
                    "color": theme["foreground"],
                    "weight": "bold",
                },
            }
        ],
        "layout": {
            "mapbox": {
                "layers": [],
                "accesstoken": "pk.eyJ1IjoiZGFlbnVwcm9ic3QiLCJhIjoiY2s3eDR2dmRyMDg0ajN0cDlkaDNmM3J0NyJ9.tcJPFQkbsVGlWpyQaKPtiw",
                "style": "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz",
                "center": {"lat": 46.8181877, "lon": 8.2275124},
                "pitch": 0,
                "zoom": 7,
            },
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "height": 600,
        },
    }


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
                "y": data[canton],
                "name": canton,
                "marker": {"color": theme["foreground"]},
                "type": "bar"
            }
            for i, canton in enumerate(data)
            if canton != "Date" and canton == "CH"
        ],
        "layout": {
            "title": "Total Cases Switzerland",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},            
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }

#
# Total cases Switzerland (prediction)
#
@app.callback(
    Output("case-ch-graph-pred", "figure"), [Input("radio-scale", "value")],
)
def update_case_ch_graph_pred(selected_scale):
    return {
        "data": [
            {
                "x": data_pred["Date"],
                "y": data_pred[canton],
                "name": canton,
                "marker": {"color": theme["foreground"]},
                "type": "bar"
            }
            for i, canton in enumerate(data)
            if canton != "Date" and canton == "CH"
        ],
        "layout": {
            "title": "Predicted Total Cases Switzerland",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff"},
            "yaxis": {"type": selected_scale, "showgrid": True, "color": "#ffffff"},    
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }

#
# Predictions: cases per canton
#
@app.callback(
    Output("case-graph-pred", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_graph_pred(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data_pred["Date"],
                "y": data_pred[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data_pred)
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

#
# Predictions: cases per canton (per 10'000 inhabitants)
#
@app.callback(
    Output("case-pc-graph-pred", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale", "value")],
)
def update_case_pc_graph_pred(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data_pred_norm["Date"],
                "y": data_pred_norm[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data_pred)
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

if __name__ == "__main__":
    app.run_server(
        debug=False,
        dev_tools_hot_reload=True,
        dev_tools_hot_reload_interval=5000,
        dev_tools_hot_reload_max_retry=30)

