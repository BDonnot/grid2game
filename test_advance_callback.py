import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from time import time
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.count = 0
app.layout = html.Div([
    html.Div('Atuomatic count'),
    dcc.Checklist(id="plus_one",
                  options=[{'label': 'Count', 'value': '1'}],
                  value=[]
                  ),
    html.P(f"{app.count}", id="display"),
    dcc.Input(id="count_to_selfloop", value=0, type="number", style={'display': 'none'}),
    dcc.Input(id="selfloop_to_count", value=0, type="number", style={'display': 'none'}),
    dcc.Input(id="to_fool_windows", value=0, type="number", style={'display': 'none'}),

], className="row")

@app.callback(
    Output("count_to_selfloop", "value"),
    Output("display", "children"),
    Input("plus_one", "value"),
    Input("selfloop_to_count", "value"),
)
def sync_input(plus_one, selfloop_to_count):
    # print("###########################")
    # print(f"sync_input, plus_one {plus_one}")
    # print(f"sync_input, selfloop_to_count {selfloop_to_count}")
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    count_to_selfloop = 0
    print(f"input_id: {input_id}")
    if input_id == "plus_one":
        count_to_selfloop = 1
        app.count += 1
    elif input_id == "selfloop_to_count":
        if selfloop_to_count == 1:
            time.sleep(1)
            count_to_selfloop = 1
            app.count += 1
    else:
        raise dash.exceptions.PreventUpdate
    display = f"{app.count}"
    # print(f"sync_input, count_to_selfloop {count_to_selfloop}")
    # print(f"sync_input, display {display}")
    return count_to_selfloop, display

@app.callback(
    # Output("selfloop_to_count", "value"),
    Output("to_fool_windows", "value"),
    Input("count_to_selfloop", "value"),
    State("plus_one", "value")
)
def selfloop(count_to_selfloop, plus_one):
    # print("###########################")
    # print(f"selfloop, count_to_selfloop {count_to_selfloop}")
    # print(f"selfloop, plus_one {plus_one}")
    print(f"count_to_selfloop : {count_to_selfloop}, plus_one: {plus_one}")
    selfloop_to_count = 0
    if count_to_selfloop and len(plus_one) > 0:
        selfloop_to_count = 1
    else:
        raise dash.exceptions.PreventUpdate
    print(f"selfloop, selfloop_to_count {selfloop_to_count}")
    # sync_input(plus_one, selfloop_to_count)
    return selfloop_to_count

@app.callback(
   Output("selfloop_to_count", "value"),
   Input("to_fool_windows", "value")
)
def fool(to_fool_windows):
    print("inside \"fool\"")
    return to_fool_windows


if __name__ == "__main__":
    app.run_server(debug=True)
