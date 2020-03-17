# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
url = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland.csv"
df = pd.read_csv(url, error_bad_lines=False)

data = df.to_dict("list")

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(
    children=[
        html.H1(children="COVID19 Cases Switzerland"),
        dcc.Graph(
            id="case graph",
            figure={
                "data": [
                    {"x": data["Date"], "y": data[canton], "name": canton}
                    for canton in data
                    if canton != "Date"
                ],
                "layout": {"title": "Cases per Canton"},
            },
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)

