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
import plotly

from grid2game.plot import PlotGrids
from grid2game.plot import PlotTemporalSeries
from grid2game.envs import Env


class VizServer:
    # TODO
    SELF_LOOP_STOP = 0
    SELF_LOOP_GO = 1
    SELF_LOOP_GOFAST = 2

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
        self.plot_grids = PlotGrids(self.env.observation_space)
        self.plot_temporal = PlotTemporalSeries(self.env)
        self.fig_load_gen = self.plot_temporal.fig_load_gen
        self.fig_line_cap = self.plot_temporal.fig_line_cap

        self.env.seed(args.env_seed)

        # internal members
        self.step_clicks = 0
        self.simulate_clicks = 0
        self.back_clicks = 0
        self.go_clicks = 0
        self.gofast_clicks = 0
        self.reset_clicks = 0
        self.nb_step_gofast = 12  # number of steps made in each frame for the "go_fast" mode
        # TODO implement the to below
        self.time_refresh = 1  # in seconds (time at which the page will be refreshed)

        # ugly hack for the date time display
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # tools to plot
        self.plot_grids.init_figs(self.env.obs, self.env.sim_obs)
        self.real_time = self.plot_grids.figure_rt
        self.forecast = self.plot_grids.figure_forecat

        # initialize the layout
        self.app.layout = self.setupLayout()

        # handle "step" button
        self.app.callback([dash.dependencies.Output("step_butt_call_act_on_env", "value")],
                          [dash.dependencies.Input("step-button", "n_clicks")],
                          state=[]
                          )(self.step_clicked)

        # handle "simulate" button
        self.app.callback([dash.dependencies.Output("simul_butt_call_act_on_env", "value")],
                          [dash.dependencies.Input("simulate-button", "n_clicks")],
                          state=[]
                          )(self.simulate_clicked)

        # handle "back" button
        self.app.callback([dash.dependencies.Output("back_butt_call_act_on_env", "value"),],
                          [dash.dependencies.Input("back-button", "n_clicks")],
                          state=[]
                          )(self.back_clicked)

        # handle "reset" button
        self.app.callback([dash.dependencies.Output("reset_butt_call_act_on_env", "value"),],
                          [dash.dependencies.Input("reset-button", "n_clicks")],
                          state=[]
                          )(self.reset_clicked)

        # handle the "go" button
        self.app.callback([dash.dependencies.Output("go_butt_call_act_on_env", "value"),],
                          [dash.dependencies.Input("go-button", "n_clicks")],
                          state=[]
                          )(self.go_clicked)

        # handle the "go" button
        self.app.callback([dash.dependencies.Output("gofast_butt_call_act_on_env", "value"),],
                          [dash.dependencies.Input("gofast-button", "n_clicks")],
                          state=[]
                          )(self.gofast_clicked)

        # handle the press to one of the button to change the units
        self.app.callback([dash.dependencies.Output("unit_trigger_rt_graph", "n_clicks"),
                           dash.dependencies.Output("unit_trigger_for_graph", "n_clicks"),
                           ],
                           [dash.dependencies.Input("line-info-dropdown", "value"),
                            dash.dependencies.Input("line-side-dropdown", "value"),
                            dash.dependencies.Input("load-info-dropdown", "value"),
                            dash.dependencies.Input("gen-info-dropdown", "value"),
                            dash.dependencies.Input("stor-info-dropdown", "value")
                           ],
                          [dash.dependencies.State("unit_trigger_rt_graph", "n_clicks"),
                           dash.dependencies.State("unit_trigger_for_graph", "n_clicks")]
                          )(self.unit_clicked)

        # handle the interaction with the graph
        self.app.callback([dash.dependencies.Output("do_display_action", "value"),
                           dash.dependencies.Output("generator_clicked", "style"),
                           dash.dependencies.Output("gen-id-hidden", "children"),
                           dash.dependencies.Output("gen-id-clicked", "children"),
                           dash.dependencies.Output("gen-dispatch", "min"),
                           dash.dependencies.Output("gen-dispatch", "max"),
                           dash.dependencies.Output("gen-dispatch", "value"),
                           dash.dependencies.Output("gen_p", "children"),
                           dash.dependencies.Output("target_disp", "children"),
                           dash.dependencies.Output("actual_disp", "children"),

                           dash.dependencies.Output("storage_clicked", "style"),
                           dash.dependencies.Output("storage-id-hidden", "children"),
                           dash.dependencies.Output("stor-id-clicked", "children"),
                           dash.dependencies.Output("storage-power-input", "min"),
                           dash.dependencies.Output("storage-power-input", "max"),
                           dash.dependencies.Output("storage-power-input", "value"),
                           dash.dependencies.Output("storage_p", "children"),
                           dash.dependencies.Output("storage_energy", "children"),

                           dash.dependencies.Output("line_clicked", "style"),
                           dash.dependencies.Output("line-id-hidden", "children"),
                           dash.dependencies.Output("line-id-clicked", "children"),
                           dash.dependencies.Output("line-status-input", "value"),
                           dash.dependencies.Output("line_flow", "children"),

                           dash.dependencies.Output("sub_clicked", "style"),
                           dash.dependencies.Output("sub-id-hidden", "children"),
                           dash.dependencies.Output("sub-id-clicked", "children"),
                           dash.dependencies.Output("graph_clicked_sub", "figure"),

                           ],
                          [dash.dependencies.Input('real-time-graph', 'clickData'),
                           dash.dependencies.Input("back-button", "n_clicks"),
                           dash.dependencies.Input("step-button", "n_clicks"),
                           dash.dependencies.Input("simulate-button", "n_clicks"),
                           dash.dependencies.Input("go-button", "n_clicks"),
                           dash.dependencies.Input("gofast-button", "n_clicks"),
                           ]
                          )(self.display_click_data)

        # handle display of the action, if needed
        self.app.callback([dash.dependencies.Output("current_action", "children"),
                           ],
                          [dash.dependencies.Input("do_display_action", "value"),
                           dash.dependencies.Input("gen-id-hidden", "children"),
                           dash.dependencies.Input('gen-dispatch', "value"),
                           dash.dependencies.Input("storage-id-hidden", "children"),
                           dash.dependencies.Input('storage-power-input', "value"),
                           dash.dependencies.Input("line-id-hidden", "children"),
                           dash.dependencies.Input('line-status-input', "value"),
                           dash.dependencies.Input('sub-id-hidden', "children"),
                           dash.dependencies.Input("graph_clicked_sub", "clickData")
                          ])(self.display_action)

        # handle triggers: the collapse of the temporal information
        # TODO do not work now !
        self.app.callback([dash.dependencies.Output("collapsetemp_trigger_temporal_figs", "n_clicks")
                           ],
                          [dash.dependencies.Input('show-temoral-graph', "value")],
                          [dash.dependencies.State("collapsetemp_trigger_temporal_figs", "n_clicks")]
                          )(self.show_temporal_graphs)

        # handle the interaction with self.env, that should be done all in one function, otherwise
        # there are concurrency issues
        self.app.callback([dash.dependencies.Output("act_on_env_trigger_rt", "n_clicks"),
                           dash.dependencies.Output("act_on_env_trigger_for", "n_clicks"),
                           dash.dependencies.Output("act_on_env_call_selfloop", "value")],
                          [dash.dependencies.Input("step_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("simul_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("back_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("reset_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("go_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("gofast_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("selfloop_call_act_on_env", "value"),
                           ]
                          )(self.handle_act_on_env)

        # self loop
        self.app.callback([dash.dependencies.Output("step-button", "className"),
                           dash.dependencies.Output("simulate-button", "className"),
                           dash.dependencies.Output("back-button", "className"),
                           dash.dependencies.Output("reset-button", "className"),
                           dash.dependencies.Output("go-button", "className"),
                           dash.dependencies.Output("selfloop_call_act_on_env", "value")],
                          [dash.dependencies.Input("act_on_env_call_selfloop", "value")]
                          )(self.self_loop_step)

        # handle triggers: refresh of the figures for real time (graph part)
        self.app.callback([dash.dependencies.Output("figrt_trigger_temporal_figs", "n_clicks"),
                           dash.dependencies.Output("figrt_trigger_rt_graph", "n_clicks"),
                           dash.dependencies.Output("figrt_trigger_for_graph", "n_clicks"),
                           ],
                          [dash.dependencies.Input("act_on_env_trigger_rt", "n_clicks")],
                          []
                          )(self.update_rt_fig)

        # handle triggers: refresh of the figures for the forecast
        self.app.callback([dash.dependencies.Output("figfor_trigger_for_graph", "n_clicks")],
                          [dash.dependencies.Input("act_on_env_trigger_for", "n_clicks"),
                           ],
                          []
                          )(self.update_simulated_fig)

        # final graph display
        # handle triggers: refresh the figures (temporal series part)
        self.app.callback([dash.dependencies.Output('temporal_graphs', "style"),
                           dash.dependencies.Output("graph_gen_load", "figure"),
                           dash.dependencies.Output("graph_flow_cap", "figure"),
                           ],
                          [dash.dependencies.Input("figrt_trigger_temporal_figs", "n_clicks"),
                           # dash.dependencies.Input("collapsetemp_trigger_temporal_figs", "n_clicks")
                          ],
                          [dash.dependencies.State('show-temoral-graph', "value")]
                          )(self.update_temporal_figs)

        # handle final graph of the real time grid
        self.app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                           dash.dependencies.Output("rt_date_time", "children")],
                          [dash.dependencies.Input("figrt_trigger_rt_graph", "n_clicks"),
                           dash.dependencies.Input("unit_trigger_rt_graph", "n_clicks"),
                           ]
                          )(self.update_rt_graph_figs)

        # handle final graph for the forecast grid
        self.app.callback([dash.dependencies.Output("simulated-graph", "figure"),
                           dash.dependencies.Output("forecast_date_time", "children")],
                          [dash.dependencies.Input("figrt_trigger_for_graph", "n_clicks"),
                           dash.dependencies.Input("figfor_trigger_for_graph", "n_clicks"),
                           dash.dependencies.Input("unit_trigger_for_graph", "n_clicks"),
                           ]
                          )(self.update_for_graph_figs)

    def run(self, debug=False):
        self.app.run_server(debug=debug)

    def setupLayout(self):
        # layout of the app
        # TODO split that in multiple subfunctions

        # Header
        title = html.H1(children='Grid2Game')
        header = html.Header(id="header", className="row w-100", children=[title])

        # App
        reset_button = html.Label("Reset",
                                  id="reset-button",
                                  n_clicks=0,
                                  className="btn btn-primary")
        reset_button_dummy = html.P("", style={'display': 'none'})

        # Controls widget
        step_button = html.Label("Step",
                                 id="step-button",
                                 n_clicks=0,
                                 className="btn btn-primary")
        simulate_button = html.Label("Simulate",
                                     id="simulate-button",
                                     n_clicks=0,
                                     className="btn btn-primary")
        back_button = html.Label("Back",
                                 id="back-button",
                                 n_clicks=0,
                                 className="btn btn-primary")
        continue_til_go = html.Label("Go",
                                     id="go-button",
                                     n_clicks=0,
                                     className="btn btn-primary")
        go_fast = html.Label("Fast",
                             id="gofast-button",
                             n_clicks=0,
                             className="btn btn-primary")
        # TODO add a button "trust assistant up to" that will play the actions suggested by the
        # TODO assistant

        show_temporal_graph = dcc.Checklist(id="show-temoral-graph",
                                            options=[{'label': '(TODO) Display time series', 'value': 'display'}],
                                            value=["display"]
                                            )
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
                                 ],
                                 value='or',
                                 clearable=False)
        
        load_info_label = html.Label("Load unit:")
        load_info = dcc.Dropdown(id='load-info-dropdown',
                                 options=[
                                     {'label': 'MW', 'value': 'p'},
                                     {'label': 'kV', 'value': 'v'},
                                     {'label': 'MVar', 'value': 'q'},
                                     {'label': 'name', 'value': 'name'},
                                     {'label': 'None', 'value': 'none'},
                                 ],
                                 value='p',
                                 clearable=False)
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
                                ],
                                value='p',
                                clearable=False)

        stor_info_label = html.Label("Stor. unit:")
        stor_info = dcc.Dropdown(id='stor-info-dropdown',
                                 options=[
                                    {'label': 'MW', 'value': 'p'},
                                    {'label': 'MWh', 'value': 'MWh'},
                                    {'label': 'None', 'value': 'none'},
                                 ],
                                 value='p',
                                 clearable=False)

        # html display
        button_css = "col-6 col-sm-6 col-md-3 col-lg-3 col-xl-1"
        reset_col = html.Div(id="reset-col", className=button_css, children=[reset_button, reset_button_dummy])
        step_col = html.Div(id="step-col", className=button_css, children=[step_button])
        sim_col = html.Div(id="sim-step-col", className=button_css, children=[simulate_button])
        back_col = html.Div(id="back-col", className=button_css, children=[back_button])
        continue_til_go_col = html.Div(id="continue_til_go-col", className=button_css, children=[continue_til_go])
        go_fast_col = html.Div(id="go_fast-col", className=button_css, children=[go_fast],
                               # style={'display': 'none'}  # TODO that do not work for now
                               )

        lineinfo_col = html.Div(id="lineinfo-col", className=button_css, children=[line_info_label, line_info])
        lineside_col = html.Div(id="lineside-col", className=button_css, children=[line_side_label, line_side])
        loadinfo_col = html.Div(id="loadinfo-col", className=button_css, children=[load_info_div])
        geninfo_col = html.Div(id="geninfo-col", className=button_css, children=[gen_info_label, gen_info])
        storinfo_col = html.Div(id="storinfo-col", className=button_css, children=[stor_info_label, stor_info])
        # storinfo_col = html.Div(id="storinfo-col", className=button_css, children=[stor_info_label, show_temporal_graph])

        change_units = html.Div(id="change_units",
                                children=[
                                    lineinfo_col,
                                    lineside_col,
                                    loadinfo_col,
                                    geninfo_col,
                                    storinfo_col,
                                    show_temporal_graph
                                ],
                                className="row",
                                )

        controls_row = html.Div(id="control-buttons",
                                className="row",
                                children=[
                                    back_col,  # TODO display back only if its possible in the self.env
                                    step_col,
                                    sim_col,
                                    continue_til_go_col,
                                    go_fast_col,
                                ])
        controls_row = html.Div(id="controls-row",
                                children=[
                                    reset_col,
                                    controls_row,
                                    change_units
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
                                style={'display': 'inline-block', 'width': '50vh', 'height': '55vh'}
                                )
        forecast_graph_label = html.H3("Forecast (t+5mins):", style={'text-align': 'center'})
        forecast_date_time = html.P("", style={'text-align': 'center'}, id="forecast_date_time")
        sim_graph_div = html.Div(id="sim_graph_div",
                                 className=graph_css,
                                 children=[
                                     forecast_graph_label,
                                     forecast_date_time,
                                     simulate_graph],

                                 style={'display': 'inline-block', 'width': '50vh', 'height': '55vh'}
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

        graph_gen_load = dcc.Graph(id="graph_gen_load",
                                   config={
                                       'displayModeBar': False,
                                       "responsive": True,
                                       "autosizable": True
                                    },

                                   style={'display': 'block'},
                                   figure=self.fig_load_gen)
        graph_flow_cap = dcc.Graph(id="graph_flow_cap",
                                   config={
                                       'displayModeBar': False,
                                       "responsive": True,
                                       "autosizable": True
                                   },
                                   style={'display': 'block'},
                                   figure=self.fig_line_cap)

        temporal_graphs = html.Div([html.Div([graph_gen_load],
                                             className=graph_css,
                                             style={'display': 'inline-block',
                                                    'width': '50vh', 'height': '47vh'}),
                                    html.Div([graph_flow_cap],
                                             className=graph_css,
                                             style={'display': 'inline-block',
                                                    'width': '50vh', 'height': '47vh'})
                                    ],
                                   className="row",
                                   id="temporal_graphs")
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
        generator_clicked = html.Div([html.P("Generator id", id="gen-id-clicked"),
                                      html.P("Redispatching:"),
                                      dcc.Input(placeholder="redispatch to apply: ",
                                                id='gen-dispatch',
                                                type='range',
                                                min=-1.0,
                                                max=1.0,
                                                ),
                                      html.P("gen_p", id="gen_p"),
                                      html.P("target_disp", id="target_disp"),
                                      html.P("actual_disp", id="actual_disp"),
                                      html.P("",
                                             id="gen-id-hidden",
                                             style={'display': 'none'}
                                             )
                                      ],
                                     id="generator_clicked",
                                     className="six columns",
                                     style={'display': 'inline-block'}
                                     )
        storage_clicked = html.Div([html.P("Storage id", id="stor-id-clicked"),
                                    html.P("Storage consumption (>=0: charging = load):"),
                                    dcc.Input(placeholder="storage power setpoint: ",
                                              id='storage-power-input',
                                              type='range',
                                              min=-1.0,
                                              max=1.0,
                                              ),
                                    html.P("storage_p", id="storage_p"),
                                    html.P("storage_energy", id="storage_energy"),
                                    html.P("",
                                           id="storage-id-hidden",
                                           style={'display': 'none'}
                                           )
                                    ],
                                   id="storage_clicked",
                                   className="six columns",
                                   style={'display': 'inline-block'}
                                   )
        line_clicked = html.Div([html.P("Line id", id="line-id-clicked"),
                                 html.P("New status:"),
                                 dcc.Dropdown(
                                     options=[
                                         {'label': "connect", 'value': "+1"},
                                         {'label': "disconnect", 'value': "-1"},
                                         {'label': "don't change", 'value': "0"},
                                     ],
                                     id='line-status-input'
                                 ),
                                 html.P("line_flow", id="line_flow"),
                                 html.P("",
                                        id="line-id-hidden",
                                        style={'display': 'none'}
                                        )
                                 ],
                                id="line_clicked",
                                className="six columns",
                                style={'display': 'inline-block'}
                                )
        sub_clicked = html.Div([html.P("sub id", id="sub-id-clicked"),
                                html.P("New Topology:"),
                                dcc.Graph(id="graph_clicked_sub",
                                          config={
                                              'displayModeBar': False,
                                              "responsive": True,
                                              "autosizable": True
                                          },
                                          style={'display': 'inline-block',
                                                 'width': '50vh', 'height': '47vh'
                                                 }
                                          ),
                                html.P("",
                                       id="sub-id-hidden",
                                       style={'display': 'none'}
                                       )
                                ],
                               id="sub_clicked",
                               className="six columns",
                               style={'display': 'inline-block'}
                               )
        layout_click = html.Div([generator_clicked,
                                 storage_clicked,
                                 line_clicked,
                                 sub_clicked],
                                className='six columns')

        interaction_and_action = html.Div([html.Br(),
                                           layout_click,
                                           action_col], className="row")

        interval_object = dcc.Interval(id='interval-component',
                                       interval=self.time_refresh * 1000,  # in milliseconds
                                       n_intervals=0
                                       )

        # hidden control button, hack for having same output for multiple callbacks
        figrt_trigger_temporal_figs = html.Label("",
                                                 id="figrt_trigger_temporal_figs",
                                                 n_clicks=0)
        collapsetemp_trigger_temporal_figs = html.Label("",
                                                        id="collapsetemp_trigger_temporal_figs",
                                                        n_clicks=0)
        unit_trigger_rt_graph = html.Label("",
                                           id="unit_trigger_rt_graph",
                                           n_clicks=0)
        unit_trigger_for_graph = html.Label("",
                                            id="unit_trigger_for_graph",
                                            n_clicks=0)
        figrt_trigger_rt_graph = html.Label("",
                                            id="figrt_trigger_rt_graph",
                                            n_clicks=0)
        figrt_trigger_for_graph = html.Label("",
                                             id="figrt_trigger_for_graph",
                                             n_clicks=0)
        figfor_trigger_for_graph = html.Label("",
                                              id="figfor_trigger_for_graph",
                                              n_clicks=0)

        step_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                              id='step_butt_call_act_on_env',
                                              type='range',
                                              min=0,
                                              max=1,
                                              )
        simul_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                               id='simul_butt_call_act_on_env',
                                               type='range',
                                               min=0,
                                               max=1,
                                               )
        back_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                              id='back_butt_call_act_on_env',
                                              type='range',
                                              min=0,
                                              max=1,
                                              )
        go_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                            id='go_butt_call_act_on_env',
                                            type='range',
                                            min=0,
                                            max=1,
                                            )
        gofast_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                                id='gofast_butt_call_act_on_env',
                                                type='range',
                                                min=0,
                                                max=1,
                                                )
        reset_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                               id='reset_butt_call_act_on_env',
                                               type='range',
                                               min=0,
                                               max=1,
                                               )
        act_on_env_call_selfloop = dcc.Input(placeholder=" ",
                                             id='act_on_env_call_selfloop',
                                             type='range',
                                             min=0,
                                             max=2,
                                             )
        selfloop_call_act_on_env = dcc.Input(placeholder=" ",
                                             id='selfloop_call_act_on_env',
                                             type='range',
                                             min=0,
                                             max=2,
                                             )
        do_display_action = dcc.Input(placeholder=" ",
                                      id='do_display_action',
                                      type='range',
                                      min=0,
                                      max=1,
                                      )

        # triggering the update of the figures
        act_on_env_trigger_rt = html.Label("",
                                           id="act_on_env_trigger_rt",
                                           n_clicks=0)
        act_on_env_trigger_for = html.Label("",
                                            id="act_on_env_trigger_for",
                                            n_clicks=0)
        hidden_interactions = html.Div([figrt_trigger_temporal_figs, collapsetemp_trigger_temporal_figs,
                                        unit_trigger_rt_graph, unit_trigger_for_graph, figrt_trigger_for_graph,
                                        figfor_trigger_for_graph, figrt_trigger_rt_graph,
                                        step_butt_call_act_on_env, simul_butt_call_act_on_env,
                                        back_butt_call_act_on_env, go_butt_call_act_on_env,
                                        gofast_butt_call_act_on_env,
                                        act_on_env_trigger_rt,
                                        act_on_env_trigger_for, reset_butt_call_act_on_env,
                                        act_on_env_call_selfloop, selfloop_call_act_on_env,
                                        do_display_action
                                        ],
                                       id="hidden_button_for_callbacks",
                                       style={'display': 'none'})
        # Final page
        layout_css = "container-fluid h-100 d-md-flex d-xl-flex flex-md-column flex-xl-column"
        layout = html.Div(id="grid2game",
                          className=layout_css,
                          children=[
                              header,
                              html.Br(),
                              controls_row,
                              html.Br(),
                              state_row,
                              html.Br(),
                              interaction_and_action,
                              html.Br(),
                              temporal_graphs,
                              interval_object,
                              hidden_interactions
                          ])
        return layout

    # handle the interaction
    def step_clicked(self, step_clicks):
        """handle the interaction for the "step" button"""
        do_step = 0
        if self.step_clicks < step_clicks:
            # "step" has been clicked
            self.step_clicks = step_clicks
            do_step = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [do_step]

    def back_clicked(self, back_clicks):
        """handle the interaction for the "back" button"""
        trigger_act_on_env = 0
        if self.back_clicks < back_clicks:
            # "back" has been clicked
            self.back_clicks = back_clicks
            trigger_act_on_env = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_act_on_env]

    def reset_clicked(self, reset_clicks):
        """handle the interaction for the "reset" button"""
        trigger_act_on_env = 0
        if self.reset_clicks < reset_clicks:
            # "back" has been clicked
            self.reset_clicks = reset_clicks
            trigger_act_on_env = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_act_on_env]

    def go_clicked(self, go_clicks):
        """handle the interaction for the "go" button"""
        if self.go_clicks < go_clicks:
            # "back" has been clicked
            self.go_clicks = go_clicks
            trigger_act_on_env = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_act_on_env]

    def gofast_clicked(self, gofast_clicks):
        """handle the interaction for the "go fast" button"""
        if self.gofast_clicks < gofast_clicks:
            # "back" has been clicked
            self.gofast_clicks = gofast_clicks
            trigger_act_on_env = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_act_on_env]

    def simulate_clicked(self, simulate_clicks):
        """handle the interaction for the "simulate" button"""
        trigger_act_on_env = 0
        if self.simulate_clicks < simulate_clicks:
            self.simulate_clicks = simulate_clicks
            # simulate has been called
            trigger_act_on_env = 1
        return [trigger_act_on_env]

    def unit_clicked(self, line_unit, line_side, load_unit, gen_unit, stor_unit,
                     trigger_rt_graph, trigger_for_graph):
        """handle the click to all button to change the units"""
        # controls the panels of the main graph of the grid
        if line_unit != self.plot_grids.line_info:
            self.plot_grids.line_info = line_unit
            self.plot_grids.update_lines_info()
        if line_side != self.plot_grids.line_side:
            self.plot_grids.line_side = line_side
            self.plot_grids.update_lines_side()
        if load_unit != self.plot_grids.load_info:
            self.plot_grids.load_info = load_unit
            self.plot_grids.update_loads_info()
        if gen_unit != self.plot_grids.gen_info:
            self.plot_grids.gen_info = gen_unit
            self.plot_grids.update_gens_info()
        if stor_unit != self.plot_grids.storage_info:
            self.plot_grids.storage_info = stor_unit
            self.plot_grids.update_storages_info()
        return [trigger_rt_graph, trigger_for_graph]

    # handle the interaction with the grid2op environment
    def handle_act_on_env(self, step_butt, simulate_butt, back_butt, reset_butt, go_butt,
                          gofast_butt,
                          self_loop):
        """
        dash do not make "synch" callbacks (two callbacks can be called at the same time),
        however, grid2op environments are not "thread safe": accessing them from different "thread"
        "coroutine" "process" is not a good idea.

        This function ensures that all functions related to the manipulation of the environment
        are done sequentially.

        see https://dash.plotly.com/advanced-callbacks, paragraph
        "Prevent Callback Execution Upon Initial Component Render"
        """
        trigger_rt = 0  # do i trigger the update of the "real time figures"
        trigger_for = 0   # do i trigger the update of the "forecast" figures
        trigger_me_again = 0  # do i call myself again

        # check which call backs triggered this calls
        # see https://dash.plotly.com/advanced-callbacks
        # section "Determining which Input has fired with dash.callback_context"
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            return [trigger_rt, trigger_for]
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # NB the checks need to be done in that order, otherwise it might lead to unexpected behaviour
        if button_id == "selfloop_call_act_on_env":
            # "go" or "gofast" has been called, i do another loop
            if self_loop == 1:
                # go has been called
                self.env.step()
            if self_loop == 2:  # TODO replace "1" and "2" here by variable names !
                # go fast have been called
                for i in range(self.nb_step_gofast):
                    if self.env.is_done:
                        break
                    self.env.step()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
            trigger_me_again = self_loop
        elif button_id == "gofast_butt_call_act_on_env":
            # "gofast" is calling, i initialize the self loop
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
            for i in range(self.nb_step_gofast):
                if self.env.is_done:
                    break
                self.env.step()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_me_again = 2
        elif button_id == "go_butt_call_act_on_env":
            # "go" is calling, i initialize the self loop
            if not self.env.is_done:
                self.env.step()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
            trigger_me_again = 1
        elif button_id == "step_butt_call_act_on_env":
            # "step" is calling
            if not self.env.is_done:
                self.env.step()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
        elif button_id == "simul_butt_call_act_on_env":
            # "simulate" is calling
            self.env.simulate()
            self.plot_grids.update_forecat(self.env.sim_obs)
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"
            trigger_for = 1
        elif button_id == "back_butt_call_act_on_env":
            # "back"" is calling
            self.env.back()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
        elif button_id == "reset_butt_call_act_on_env":
            # "reset" is calling
            self.env.reset()
            self.update_obs_fig()  # TODO maybe not here, i don't know :thinking:
            trigger_rt = 1
            trigger_for = 1
        else:
            # nothing really called me, so i stop here
            raise dash.exceptions.PreventUpdate

        return [trigger_rt, trigger_for, trigger_me_again]

    def self_loop_step(self, act_on_env_call_selfloop):
        """
        Allows to do a "self loop" on act_on_env step.
        This is usefull in a "go fast" or in a "go" mode
        """
        if act_on_env_call_selfloop is None or act_on_env_call_selfloop == 0:
            # there is not self loop, i stop
            raise dash.exceptions.PreventUpdate

        button_shape = "btn btn-primary"
        go_button_shape = "btn btn-primary"
        selfloop_call_act_on_env = 0

        # check if i am in a self loop or not
        if self.gofast_clicks % 2 == 1:
            # i'm in the "go fast" mode
            button_shape = "btn btn-secondary"
            go_button_shape = "btn btn-secondary"
            selfloop_call_act_on_env = 2
        elif self.go_clicks % 2 == 1:
            # i'm not in a "self loop", button should be updated correctly
            button_shape = "btn btn-secondary"
            selfloop_call_act_on_env = 1

        return [button_shape, button_shape, button_shape, button_shape, go_button_shape,
                selfloop_call_act_on_env]

    # handle the layout
    def update_rt_fig(self, env_act):
        """the real time figures need to be updated"""
        if env_act is not None and env_act > 0:
            trigger_temporal_figs = 1
            trigger_rt_graph = 1
            trigger_for_graph = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_temporal_figs, trigger_rt_graph, trigger_for_graph]

    def update_simulated_fig(self, env_act):
        """the simulate figures need to updated"""
        if env_act is not None and env_act > 0:
            trigger_for_graph = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_for_graph]

    def show_temporal_graphs(self, show_temporal_graph, trigger_temporal_figs):
        """handles the action that displays (or not) the time series graphs"""
        if (show_temporal_graph is None or show_temporal_graph == 0) and \
                (trigger_temporal_figs is None or trigger_temporal_figs == 0):
            raise dash.exceptions.PreventUpdate
        return [trigger_temporal_figs]

    # end point of the trigger stuff: what is displayed on the page !
    def update_temporal_figs(self, figrt_trigger, graph_state):
        # TODO collapsetemp_trigger is deactivated otherwise it does not work
        display_mode = {'display': 'none'}
        if graph_state:
            # i should display the figure
            self.plot_temporal.update_layout_height()  # otherwise figures shrink when trigger is called
            self.plot_temporal.update_trace()
            display_mode = {'display': 'block'}
        else:
            raise dash.exceptions.PreventUpdate
        return [display_mode, self.fig_load_gen, self.fig_line_cap]

    def update_rt_graph_figs(self, figrt_trigger, unit_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (unit_trigger is None or unit_trigger == 0):
            # nothing really triggered this call
            raise dash.exceptions.PreventUpdate
        return [self.real_time,  self.rt_datetime]

    def update_for_graph_figs(self, figrt_trigger, figfor_trigger, unit_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (figfor_trigger is None or figfor_trigger == 0) and \
                (unit_trigger is None or unit_trigger == 0):
            # nothing really triggered this call
            raise dash.exceptions.PreventUpdate
        return [self.forecast, self.for_datetime]

    # auxiliary functions
    def update_obs_fig(self):
        self.plot_grids.update_rt(self.env.obs)
        self.plot_grids.update_forecat(self.env.sim_obs)
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

    # self.plot_temporal.fig_load_gen, self.plot_temporal.fig_line_cap
    def display_action(self,
                       do_display,
                       gen_id, redisp,
                       stor_id, storage_p,
                       line_id, line_status,
                       sub_id, clicked_sub_fig):
        """
        modify the action taken based on the inputs,
        then displays the action (as text)"""
        # TODO handle better the action (this is ugly to access self.env._current_action from here)

        if not do_display:
            # i should not display the action
            res = [""]
        else:
            # i need to display the action
            is_modif = False
            if gen_id != "":
                self.env._current_action.redispatch = [(int(gen_id), float(redisp))]
                is_modif = True
            if stor_id != "":
                self.env._current_action.storage_p = [(int(stor_id), float(storage_p))]
                is_modif = True
            if line_id != "" and line_status is not None:
                self.env._current_action.line_set_status = [(int(line_id), int(line_status))]
                is_modif = True
            if sub_id != "":
                if clicked_sub_fig is not None:
                    # i modified a substation topology
                    is_modif = True
                    # TODO update the action AND the figure of the substation !!!!
            if not is_modif:
                raise dash.exceptions.PreventUpdate

            # TODO optim here to save that if not needed because nothing has changed
            res = [f"{self.env.current_action}"]
        return res

    def display_click_data(self, clickData,
                           back_clicked, step_clicked, simulate_clicked, go_clicked,
                           gofast_clicked):
        """display the intearction window when the real time graph is clicked on"""
        do_display_action = 0
        style_gen_input = {'display': 'none'}
        gen_id_clicked = ""
        gen_res = ["", -1., 1., 0., "gen_p", "target_disp", "actual_disp"]

        style_storage_input = {'display': 'none'}
        storage_id_clicked = ""
        storage_res = ["", -1., 1., 0., "storage_power", "storage_capaticy"]

        style_line_input = {'display': 'none'}
        line_id_clicked = ""
        line_res = ["", 0, "flow"]

        style_sub_input = {'display': 'none'}
        sub_id_clicked = ""
        sub_res = ["", self.plot_grids.sub_fig]

        # check which call backs triggered this calls
        # see https://dash.plotly.com/advanced-callbacks
        # section "Determining which Input has fired with dash.callback_context"
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            # so no action displayed
            return [do_display_action,
                    style_gen_input, gen_id_clicked, *gen_res,
                    style_storage_input, storage_id_clicked, *storage_res,
                    style_line_input, line_id_clicked, *line_res,
                    style_sub_input, sub_id_clicked, *sub_res
                    ]

        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # https://stackoverflow.com/questions/50213761/changing-visibility-of-a-dash-component-by-updating-other-component
        if clickData is None:
            # i never clicked on any data
            do_display_action = 0
        elif button_id == "step-button" or button_id == "simulate-button" or \
                button_id == "go-button" or button_id == "gofast-button" or\
                button_id == "back-button":
            # i never clicked on simulate, step, go, gofast or back
            do_display_action = 0
        else:
            obj_type, obj_id, res_type = self.plot_grids.get_object_clicked(clickData)
            if obj_type == "gen":
                gen_id_clicked = f"{obj_id}"
                style_gen_input = {'display': 'inline-block'}
                gen_res = res_type
                do_display_action = 1
            elif obj_type == "stor":
                storage_id_clicked = f"{obj_id}"
                style_storage_input = {'display': 'inline-block'}
                storage_res = res_type
                do_display_action = 1
            elif obj_type == "line":
                line_id_clicked = f"{obj_id}"
                style_line_input = {'display': 'inline-block'}
                line_res = res_type
                do_display_action = 1
            elif obj_type == "sub":
                sub_id_clicked = f"{obj_id}"
                style_sub_input = {'display': 'inline-block'}
                sub_res = res_type
                do_display_action = 1
            else:
                raise dash.exceptions.PreventUpdate
        return [do_display_action,
                style_gen_input, gen_id_clicked, *gen_res,
                style_storage_input, storage_id_clicked, *storage_res,
                style_line_input, line_id_clicked, *line_res,
                style_sub_input, sub_id_clicked, *sub_res
                ]
