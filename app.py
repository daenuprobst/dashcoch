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

url_demo = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/demographics.csv"
df_demo = pd.read_csv(url_demo, error_bad_lines=False, index_col=0)

# Wrangle the data
data = df.to_dict("list")
data_norm = {
    str(canton): [
        round(i, 2) for i in data[canton] / df_demo["Population"][canton] * 10000
    ]
    for canton in data
    if canton != "Date"
}
data_norm["Date"] = data["Date"]

# Some nice differentiable colors for the cantons + CH
colors = [
    "#8b4513",
    "#228b22",
    "#808000",
    "#483d8b",
    "#bc8f8f",
    "#008080",
    "#4682b4",
    "#000080",
    "#9acd32",
    "#800080",
    "#b03060",
    "#66cdaa",
    "#ff4500",
    "#ffa500",
    "#ffa07a",
    "#7fff00",
    "#00fa9a",
    "#8a2be2",
    "#dc143c",
    "#0000ff",
    "#ff00ff",
    "#1e90ff",
    "#f0e68c",
    "#dda0dd",
    "#add8e6",
    "#ff1493",
    "#000000",
]


# General app settings
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Swiss COVID19 Tracker"

# Show the data
app.layout = html.Div(
    children=[
        html.H3(children="COVID19 Cases Switzerland"),
        dcc.RadioItems(
            id="radio-scale",
            options=[
                {"label": "Linear Scale", "value": "linear"},
                {"label": "Logarithmic Scale", "value": "log"},
            ],
            value="linear",
            labelStyle={"display": "inline-block"},
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
        html.H4(children="Raw Data"),
        dash_table.DataTable(
            id="table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
        ),
    ]
)

# Callbacks
@app.callback(Output("case-graph", "figure"), [Input("radio-scale", "value")])
def update_case_graph(selected_scale):
    return {
        "data": [
            {
                "x": data["Date"],
                "y": data[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data)
            if canton != "Date" and canton != "CH"
        ],
        "layout": {
            "title": "Cases per Canton",
            "height": 750,
            "yaxis": {"type": selected_scale},
        },
    }


@app.callback(Output("case-pc-graph", "figure"), [Input("radio-scale", "value")])
def update_case_pc_graph(selected_scale):
    return {
        "data": [
            {
                "x": data_norm["Date"],
                "y": data_norm[canton],
                "name": canton,
                "marker": {"color": colors[i - 1]},
            }
            for i, canton in enumerate(data)
            if canton != "Date" and canton != "CH"
        ],
        "layout": {
            "title": "Cases per Canton (per 10,000 Inhabitants)",
            "height": 750,
            "yaxis": {"type": selected_scale},
        },
    }


@app.callback(Output("case-ch-graph", "figure"), [Input("radio-scale", "value")])
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
        },
    }


if __name__ == "__main__":
    app.run_server()

