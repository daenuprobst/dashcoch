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

# Wrangle the data
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

theme = {"background": "#ecf0f1", "foreground": "#222222", "accent": "#9b59b6"}


# General app settings
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Swiss COVID19 Tracker"

# Show the data
app.layout = html.Div(
    style={"backgroundColor": theme["background"]},
    children=[
        html.H3(children="COVID19 Cases Switzerland", style={"color": theme["accent"]}),
        dcc.RadioItems(
            id="radio-scale",
            options=[
                {"label": "Linear Scale", "value": "linear"},
                {"label": "Logarithmic Scale", "value": "log"},
            ],
            value="linear",
            labelStyle={"display": "inline-block", "color": theme["foreground"]},
        ),
        dcc.Dropdown(
            id="dropdown-cantons",
            options=[{"label": canton, "value": canton} for canton in canton_labels],
            value=canton_labels,
            multi=True,
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
        html.Div(children=[dcc.Graph(id="case-ch-graph")]),
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

# Callbacks
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
            "yaxis": {"type": selected_scale},
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
            "yaxis": {"type": selected_scale},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


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
            "yaxis": {"type": selected_scale},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


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
            "yaxis": {"type": selected_scale},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


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
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data)
            if canton != "Date" and canton == "CH"
        ],
        "layout": {
            "title": "Total Cases Switzerland",
            "height": 300,
            "yaxis": {"type": selected_scale},
            "plot_bgcolor": theme["background"],
            "paper_bgcolor": theme["background"],
            "font": {"color": theme["foreground"]},
        },
    }


if __name__ == "__main__":
    app.run_server(debug=False)

