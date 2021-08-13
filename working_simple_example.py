import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import time
import datetime

# see http://yaaics.blogspot.com/2019/03/circular-references-in-plotlydash.html

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


class Compute(object):
    """simple class to simulate a relatively heavy computation (typically env.step or env.reset etc.)"""
    def __init__(self):
        self.__is_computing = False
        self.__computation_started = False
        self.count = 0

    def heavy_compute(self):
        if not self.__computation_started:
            return 0
        if self.__is_computing:
            return 0
        self.__is_computing = True
        time.sleep(1)
        # a debug printer to make sure i have at least 1s between two calls
        print(f"ending comptuation at {datetime.datetime.now():%H:%M:%S.%f}")
        self.count += 1
        self.__is_computing = False
        return 1

    def is_computing(self):
        return self.__is_computing

    def start_computation(self):
        self.__computation_started = True

    def stop_computation(self):
        self.__computation_started = False

    def needs_compute(self):
        return self.__computation_started


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.computer = Compute()
app.layout = html.Div([
    html.Div('Atuomatic count'),
    dcc.Checklist(id="manual_start_stop",
                  options=[{'label': 'Count', 'value': '1'}],
                  value=[]
                  ),
    html.P(f"{app.computer.count}", id="display"),  # just display the results of the comptuation as a text
    dcc.Input(id="start_computation_id", value=0, type="number", style={'display': 'none'}),
    dcc.Interval(id="timer", interval=100.),
    dcc.Input(id="update_after_computation", value=0, type="number", style={'display': 'none'}),
], className="row")


def update_webpage(update_after_computation):
    # update the state of the app based on the results of some computations
    display = f"{app.computer.count}"
    return [display]


def start_computation(manual_start_stop, timer):
    # this is called to dispatch whether or not a computation
    # needs to be started based on:
    # - the state of the check box `manual_start_stop`
    # - the timer
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == "manual_start_stop":
        # manual user click on the check box => i start or stop the computation
        if len(manual_start_stop):
            # the "tick" box is checked, so i start the computation
            app.computer.start_computation()
        else:
            # the tick box is unchecked, so i stop the computation
            app.computer.stop_computation()

    if not app.computer.needs_compute():
        # don't start the computation if not needed
        raise dash.exceptions.PreventUpdate

    # computation
    start_computation_id = 1
    return [start_computation_id]


def heavy_computation_wrapper(start_computation_id):
    # simulate a "state" of the application that depends on the computation
    if not app.computer.is_computing():
        app.computer.heavy_compute()
    update_after_computation = 1
    return [update_after_computation]


app.callback([Output("display", "children")],
             [Input("update_after_computation", "value")])(update_webpage)

app.callback([Output("start_computation_id", "value")],
             [Input("manual_start_stop", "value"),
              Input("timer", "n_intervals")]
             )(start_computation)

app.callback([Output("update_after_computation", "value")],
             [Input("start_computation_id", "value")]
             )(heavy_computation_wrapper)


if __name__ == "__main__":
    app.run_server(debug=True)
