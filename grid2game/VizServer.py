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
import json

import grid2op
from grid2game.plot import Plot
from grid2game.envs import Env


class VizServer:
    def __init__(self, args):
        meta_tags=[
            {
                'name': 'grid2game',
                'content': 'Interactive plots for grdi2op'
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
                "integrity": "sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n",
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

        # create the dash app
        self.app = dash.Dash(__name__,
                             meta_tags=meta_tags,
                             assets_folder=assets_dir,
                             external_stylesheets=external_stylesheets,
                             external_scripts=external_scripts)

        # create the grid2op related things
        self.env = Env(args.env_name, test=args.is_test)
        self.plot_helper = Plot(self.env.observation_space)

        self.step_clicks = 0
        self.simulate_clicks = 0
        self.line_info = "rho"
        self.load_info = "p"
        self.gen_info = "p"
        self.env.seed(args.env_seed)
        self.plot_helper.init_figs(self.env.obs, self.env.sim_obs)
        self.real_time = self.plot_helper.figure_rt
        self.forecast = self.plot_helper.figure_forecat

        # ugly hack for the date time display
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # initialize the layout
        self.app.layout = self.setupLayout()

        # Register controls update callback (unit information, step and simulate)
        self.app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                           dash.dependencies.Output("simulated-graph", "figure"),
                           dash.dependencies.Output("rt_date_time", "children"),
                           dash.dependencies.Output("forecast_date_time", "children"),
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

        # register callbacks for when a data is clicked on
        self.app.callback([dash.dependencies.Output("generator_clicked", "style"),
                           dash.dependencies.Output("gen-id-hidden", "children"),
                           dash.dependencies.Output("gen-id-clicked", "children"),
                           dash.dependencies.Output("gen-dispatch", "min"),
                           dash.dependencies.Output("gen-dispatch", "max"),
                           dash.dependencies.Output("gen-dispatch", "value"),
                           ],
                          [dash.dependencies.Input("real-time-graph", "clickData")])(self.display_click_data)

        # print the current action
        self.app.callback([dash.dependencies.Output("current_action", "children"),
                           ],
                          [
                            dash.dependencies.Input("gen-id-hidden", "children"),
                            dash.dependencies.Input('gen-dispatch', "value"),
                          ])(self.display_action)

    def setupLayout(self):
        # layout of the app

        # Header
        title = html.H1(children='Grid2Game')
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
        # TODO add a button "trust assistant up to" that will play the actions suggested by the
        # TODO assistant

        # change the units
        # TODO make that disapearing / appearing based on a button "show options" for example
        line_info_label = html.Label("Line unit:")
        line_info = dcc.Dropdown(id='line-info-dropdown',
            options=[
                {'label': 'Capacity', 'value': 'rho'},
                {'label': 'A', 'value': 'a'},
                {'label': 'MW', 'value': 'p'},
                {'label': 'kV', 'value': 'v'},
                {'label': 'MVAr', 'value': 'q'},
                {'label': 'thermal limit', 'value': 'th_lim'},
                {'label': 'cooldown', 'value': 'cooldown'},
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
                                     {'label': 'MW', 'value': 'p'},
                                     {'label': 'kV', 'value': 'v'},
                                     {'label': 'MVar', 'value': 'q'},
                                     {'label': 'name', 'value': 'name'},
                                     {'label': 'None', 'value': 'none'},
                                 ], value='p', clearable=False)
        load_info_div = html.Div(id="load-info", children=[load_info_label, load_info])

        gen_info_label = html.Label("Gen. unit:")
        gen_info = dcc.Dropdown(id='gen-info-dropdown',
                                options=[
                                    {'label': 'MW', 'value': 'p'},
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
                                    {'label': 'MW', 'value': 'p'},
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
        real_time_graph = dcc.Graph(id="real-time-graph",
                                    # className="w-100 h-100",
                                    config={
                                        'displayModeBar': False,
                                        "responsive": True,
                                        "autosizable": True
                                    },
                                    figure=self.real_time)
        simulate_graph = dcc.Graph(id="simulated-graph",
                                   # className="w-100 h-100",
                                   config={
                                       'displayModeBar': False,
                                       "responsive": True,
                                       "autosizable": True
                                   },
                                   figure=self.forecast)

        graph_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-7 "\
                    "order-last order-sm-last order-md-last order-xl-frist " \
                    "d-md-flex flex-md-grow-1 d-xl-flex flex-xl-grow-1"
        graph_css = "six columns"
        rt_graph_label = html.H3("Real time observation:", style={'text-align': 'center'})
        rt_date_time = html.P("", style={'text-align': 'center'}, id="rt_date_time")
        rt_graph_div = html.Div(id="rt_graph_div",
                                className=graph_css,
                                children=[
                                    rt_graph_label,
                                    rt_date_time,
                                    real_time_graph],
                                style={'display': 'inline-block', 'width': '50vh', 'height': '48vh'}
                                )
        forecast_graph_label = html.H3("Forecast (t+5mins):", style={'text-align': 'center'})
        forecast_date_time = html.P("", style={'text-align': 'center'}, id="forecast_date_time")
        sim_graph_div = html.Div(id="sim_graph_div",
                                 className=graph_css,
                                 children=[
                                     forecast_graph_label,
                                     forecast_date_time,
                                     simulate_graph],

                                 style={'display': 'inline-block', 'width': '50vh', 'height': '48vh'}
                                 )

        graph_col = html.Div(id="graph-col",
                             children=[
                                 rt_graph_div,
                                 sim_graph_div
                             ],
                             className="row",
                             # style={'display': 'inline-block'}  # to allow stacking next to each other
                             )

        ## Grid state widget
        row_css = "row d-xl-flex flex-xl-grow-1"
        state_row = html.Div(id="state-row", className=row_css, children=[
            graph_col
        ])

        # TODO temporal indicator for cumulated load / generator, and generator by types
        # TODO temporal indicator of average flows on lines, with min / max flow

        # page to click the data
        # see https://dash.plotly.com/interactive-graphing
        # TODO layout for the action made:
        # action on generator (redispatch)
        # action on storage (produce / absorb power)
        # action on line (connection / disconnection)
        # action on substation (later maybe)
        # print the action
        # reset the action

        # ### Action widget
        current_action = html.Pre(id="current_action")
        action_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-5 " \
                     "order-first order-sm-first order-md-first order-xl-last"
        action_css = "six columns"
        action_col = html.Div(id="action_widget",
                              className=action_css,
                              children=[
                                  html.P("Current action"),
                                  current_action,
                              ],
                              style={'display': 'inline-block'}
                              )

        styles = {
            'pre': {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }
        }
        generator_clicked = html.Div([html.P("Generator id",
                                             id="gen-id-clicked"),
                                      dcc.Input(placeholder="redispatch to apply: ",
                                                id='gen-dispatch',
                                                type='range',
                                                min=-1.0,
                                                max=1.0,
                                                ),
                                      html.P("",
                                             id="gen-id-hidden",
                                             style={'display': 'none'}
                                             )
                                      ],
                                     id="generator_clicked",
                                     className="six columns",
                                     style={'display': 'inline-block'}
                                     )
        layout_click = html.Div([generator_clicked,
            # dcc.Markdown("""
            #             **Click Data**
            #
            #             Click on points in the graph.
            #         """),
            # html.Div([
            #     dcc.Graph(id="clicked_graph_fig",
            #               config={
            #                   'displayModeBar': False,
            #                   "responsive": True,
            #                   "autosizable": True
            #               },
            #               )],
            #     id="clicked-state",
            #     style={'display': 'block'}
            # )
        ], className='six columns')

        interaction_and_action = html.Div([layout_click, action_col], className="row")

        # Final page
        layout_css = "container-fluid h-100 d-md-flex d-xl-flex flex-md-column flex-xl-column"
        layout = html.Div(id="grid2game",
                          className=layout_css,
                          children=[
                              header,
                              controls_row,
                              html.Hr(),
                              state_row,
                              html.Hr(),
                              interaction_and_action
                          ])
        return layout

    def display_action(self, gen_id, redisp):
        if gen_id != "":
            # TODO handle better the action (this is ugly to handle it from here!)

            # TODO initialize the value to the last seen value for the dispatch, and not the
            # value in the observation
            self.env._current_action.redispatch = [(int(gen_id), float(redisp))]

        return [self.env.current_action.__str__()]

    def display_click_data(self, clickData):
        fig, obj_type, obj_id, res_type = self.plot_helper.get_object_clicked(clickData)
        style_gen_input = {'display': 'none'}
        gen_id_clicked = ""
        gen_res = ["Generator id", -1., 1., 0.]  # gen_id, min_redisp_val, max_redisp_val, redisp_val

        # https://stackoverflow.com/questions/50213761/changing-visibility-of-a-dash-component-by-updating-other-component
        if clickData is not None and obj_type == "gen":
            gen_id_clicked = f"{obj_id}"
            style_gen_input = {'display': 'inline-block'}
            gen_res = res_type
        # return: gen_style, gen_id, min_val, max_val
        return [style_gen_input, gen_id_clicked, *gen_res]

    def controlTriggers(self, step_clicks, simulate_clicks,
                        line_unit, line_side, load_unit, gen_unit, stor_unit):
        # controls the panels of the main graph of the grid
        if line_unit != self.plot_helper.line_info:
            self.plot_helper.line_info = line_unit
            self.plot_helper.update_lines_info()
        if line_side != self.plot_helper.line_side:
            self.plot_helper.line_side = line_side
            self.plot_helper.update_lines_side()
        if load_unit != self.plot_helper.load_info:
            self.plot_helper.load_info = load_unit
            self.plot_helper.update_loads_info()
        if gen_unit != self.plot_helper.gen_info:
            self.plot_helper.gen_info = gen_unit
            self.plot_helper.update_gens_info()
        if stor_unit != self.plot_helper.storage_info:
            self.plot_helper.storage_info = stor_unit
            self.plot_helper.update_storages_info()

        # "step" has been clicked
        if self.step_clicks < step_clicks:
            self.step_clicks = step_clicks
            self.env.step()
            self.plot_helper.update_rt(self.env.obs)
            self.plot_helper.update_forecat(self.env.sim_obs)
            self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        if self.simulate_clicks < simulate_clicks:
            self.env.simulate()
            self.plot_helper.update_forecat(self.env.sim_obs)
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # TODO ugly way to display the date and time ...
        return [self.real_time, self.forecast, self.rt_datetime, self.for_datetime, self.env.current_action.__str__()]

    def run(self, debug=False):
        self.app.run_server(debug=debug)
