# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import os
import dash
import dash_core_components as dcc
import dash_html_components as html

import grid2op
from grid2game.plot import Plot
from grid2game.envs import Env


class VizServer:
    def __init__(self, args):
        meta_tags=[
            {
                'name': 'gridopviz',
                'content': 'Viz tool for grdi2op'
            },
            {
                'http-equiv': 'X-UA-Compatible',
                'content': 'IE=edge'
            },
            {
                'name': 'viewport',
                'content': 'width=device-width, initial-scale=1.0'
            }
        ]
        external_stylesheets = [
            {
                "rel": "stylesheet",
                "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
                "integrity": "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
                "crossorigin": "anonymous"
            }
        ]
        external_scripts = [
            {
                "src": "https://code.jquery.com/jquery-3.4.1.slim.min.js",
                "integrity" : "sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n",
                "crossorigin": "anonymous"
            },
            {
                "src": "https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js",
                "integrity": "sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo",
                "crossorigin": "anonymous"
            },
            {
                "src": "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js",
                "integrity": "sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6",
                "crossorigin": "anonymous"
            }
        ]
        assets_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "assets")
        )
        self.app = dash.Dash(__name__,
                             meta_tags=meta_tags,
                             assets_folder=assets_dir,
                             external_stylesheets=external_stylesheets,
                             external_scripts=external_scripts)
        # self.episode = self.load(args)
        self.env = Env(args.env_name, test=args.is_test)
        self.plot_helper = Plot(self.env.observation_space)
        self.app.layout = self.setupLayout()

        # self.plotter = PlotPlotly(observation_space=self.plot_helper, responsive=True)
        self.step_clicks = 0
        self.simulate_clicks = 0
        self.line_info = "rho"
        self.load_info = "p"
        self.gen_info = "p"
        self.env.seed(args.env_seed)

        self.real_time = self.plot_helper.plot_rt(self.env.obs)
        self.forecast = self.plot_helper.plot_forecat(self.env.sim_obs)

        # Register controls update callback
        self.app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                           dash.dependencies.Output("simulated-graph", "figure"),
                           ],
                          [dash.dependencies.Input("step", "n_clicks"),
                           dash.dependencies.Input("simulate", "n_clicks"),
                           dash.dependencies.Input("line-info-dropdown", "value"),
                           dash.dependencies.Input("line-side-dropdown", "value"),
                           dash.dependencies.Input("load-info-dropdown", "value"),
                           dash.dependencies.Input("gen-info-dropdown", "value"),
                           dash.dependencies.Input("stor-info-dropdown", "value")
                           ],
                          )(self.controlTriggers)

    def setupLayout(self):
        # Header
        title = html.H1(children='Viz demo')
        header = html.Header(id="header", className="row w-100", children=[title])

        # App
        # Controls widget
        step_button = html.Label("Step",
                                 id="step",
                                 n_clicks=0,
                                 className="btn btn-primary")
        simulate_button = html.Label("Simulate",
                                     id="simulate",
                                     n_clicks=0,
                                     className="btn btn-primary")

        # change the units
        line_info_label = html.Label("Line unit:")
        line_info = dcc.Dropdown(id='line-info-dropdown',
            options=[
                {'label': 'Capacity', 'value': 'rho'},
                {'label': 'A', 'value': 'a'},
                {'label': 'W', 'value': 'p'},
                {'label': 'kV', 'value': 'v'},
                {'label': 'MVAr', 'value': 'q'},
                {'label': 'thermal limit', 'value': 'th_lim'},
                {'label': 'coodown', 'value': 'cooldown'},
                {'label': '# step overflow', 'value': 'timestep_overflow'},
                {'label': 'name', 'value': 'name'},
                {'label': 'None', 'value': 'none'},
            ], value='rho', clearable=False)

        line_side_label = html.Label("Line side:")
        line_side = dcc.Dropdown(id='line-side-dropdown',
            options=[
                {'label': 'Origin', 'value': 'or'},
                {'label': 'Extremity', 'value': 'ex'},
                {'label': 'Both', 'value': 'both'},
                {'label': 'None', 'value': 'none'},
            ], value='or', clearable=False)
        
        load_info_label = html.Label("Load unit:")
        load_info = dcc.Dropdown(id='load-info-dropdown',
                                 options=[
                                     {'label': 'W', 'value': 'p'},
                                     {'label': 'kV', 'value': 'v'},
                                     {'label': 'MVar', 'value': 'q'},
                                     {'label': 'name', 'value': 'name'},
                                     {'label': 'None', 'value': 'none'},
                                 ], value='p', clearable=False)
        load_info_div = html.Div(id="load-info", children=[load_info_label, load_info])

        gen_info_label = html.Label("Gen. unit:")
        gen_info = dcc.Dropdown(id='gen-info-dropdown',
                                options=[
                                    {'label': 'W', 'value': 'p'},
                                    {'label': 'kV', 'value': 'v'},
                                    {'label': 'MVar', 'value': 'q'},
                                    {'label': 'name', 'value': 'name'},
                                    {'label': 'type', 'value': 'type'},
                                    {'label': 'ramp_down', 'value': 'ramp_down'},
                                    {'label': 'ramp_up', 'value': 'ramp_up'},
                                    {'label': 'target_dispatch', 'value': 'target_dispatch'},
                                    {'label': 'actual_dispatch', 'value': 'actual_dispatch'},
                                    {'label': 'None', 'value': 'none'},
                                ], value='p', clearable=False)

        stor_info_label = html.Label("Stor. unit:")
        stor_info = dcc.Dropdown(id='stor-info-dropdown',
                                options=[
                                    {'label': 'W', 'value': 'p'},
                                    {'label': 'MWh', 'value': 'MWh'},
                                    {'label': 'None', 'value': 'none'},
                                ], value='p', clearable=False)

        # html display
        button_css = "col-6 col-sm-6 col-md-3 col-lg-3 col-xl-1"
        step_col = html.Div(id="step-col", className=button_css, children=[step_button])
        sim_col = html.Div(id="sim-step-col", className=button_css, children=[simulate_button])
        lineinfo_col = html.Div(id="lineinfo-col", className=button_css, children=[line_info_label, line_info])
        lineside_col = html.Div(id="lineside-col", className=button_css, children=[line_side_label, line_side])
        loadinfo_col = html.Div(id="loadinfo-col", className=button_css, children=[load_info_div])
        geninfo_col = html.Div(id="geninfo-col", className=button_css, children=[gen_info_label, gen_info])
        storinfo_col = html.Div(id="storinfo-col", className=button_css, children=[stor_info_label, stor_info])
        controls_row = html.Div(id="controls-row", className="row", children=[
            step_col,
            sim_col,
            lineinfo_col,
            lineside_col,
            loadinfo_col,
            geninfo_col,
            storinfo_col,
        ])

        ### Graph widget
        real_time_graph = dcc.Graph(id="real-time-graph", className="w-100 h-100",
                          config={
                              'displayModeBar': False,
                              "responsive": True,
                              "autosizable": True
                          })
        simulate_graph = dcc.Graph(id="simulated-graph", className="w-100 h-100",
                          config={
                              'displayModeBar': False,
                              "responsive": True,
                              "autosizable": True
                          })
        graph_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-7 "\
                      "order-last order-sm-last order-md-last order-xl-frist " \
                      "d-md-flex flex-md-grow-1 d-xl-flex flex-xl-grow-1"
        rt_graph_label = html.Label("Real time observation:", style={'text-align': 'center'})
        rt_graph_div = html.Div(id="rt_graph_div", className=graph_css,
                                children=[
                                    rt_graph_label,
                                    real_time_graph],
                                # style={'display': 'inline-block'}  # to allow stacking next to each other
                                )
        forecast_graph_label = html.Label("Forecast (t+5mins):", style={'text-align': 'center'})
        sim_graph_div = html.Div(id="sim_graph_div",
                                 className=graph_css,
                                 children=[
                                     forecast_graph_label,
                                     simulate_graph],
                                 # style={'display': 'inline-block'}  # to allow stacking next to each other
                                 )

        graph_col = html.Div(id="graph-col",
                             children=[
                                 rt_graph_div,
                                 sim_graph_div
                             ],
                             style={'display': 'inline-block'}  # to allow stacking next to each other
                             )

        # ### Action widget
        last_action = html.Pre(id="last-action")
        next_action = html.Pre(id="next-action")
        action_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-5 " \
                     "order-first order-sm-first order-md-first order-xl-last"
        action_col = html.Div(id="action_widget", className=action_css, children=[
            last_action,
            next_action
        ])

        ## Grid state widget
        row_css = "row d-xl-flex flex-xl-grow-1"
        state_row = html.Div(id="state-row", className=row_css, children=[
            graph_col,
            action_col
        ])

        # Final page
        layout_css = "container-fluid h-100 d-md-flex d-xl-flex flex-md-column flex-xl-column"
        layout = html.Div(id="grid2game", className=layout_css,
                          children=[
                              header,
                              controls_row,
                              state_row
                          ])
        return layout

    def updateAction(self, step):
        # TODO it's not working anymore
        prev_step = step - 1
        prev_act = self.env.action_space()  # TODO
        curr_act = self.env.action_space()  # TODO
        if prev_step >= 0:
            html_prev_act = [html.P("Previous action:"), html.P(str(prev_act))]
        else:
            html_prev_act = [html.P("Previous action:"), html.P("N/A")]
        html_curr_act = [html.P("Next Action:"), html.P(str(curr_act))]
        return [html_prev_act, html_curr_act]

    def controlTriggers(self, step_clicks, simulate_clicks,
                        line_unit, line_side, load_unit, gen_unit, stor_unit):
        # Store units
        # TODO optimize to recompute only the right stuff (and not everything everytime like today)
        self.plot_helper.line_info = line_unit
        self.plot_helper.line_side = line_side
        self.plot_helper.load_info = load_unit
        self.plot_helper.gen_info = gen_unit
        self.plot_helper.storage_info = stor_unit

        # "step" has been clicked
        if self.step_clicks < step_clicks:
            self.step_clicks = step_clicks
            self.env.step()

        if self.simulate_clicks < simulate_clicks:
            self.env.simulate()

        # regenerate the graphs
        self.real_time = self.plot_helper.plot_rt(self.env.obs)
        self.forecast = self.plot_helper.plot_forecat(self.env.sim_obs)
        return [self.real_time, self.forecast]

    def run(self, debug=False):
        self.app.run_server(debug=debug)
