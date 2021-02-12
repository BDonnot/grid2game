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
        self.continue_clicks = 0
        self.go_fast_clicks = 0
        self.reset_clicks = 0
        self.time_refresh = 1  # in seconds (time at which the page will be refreshed)
        self.is_continue_mode = False
        self.is_go_fast = False
        self.nb_step_gofast = 12  # number of steps made in each frame for the "go_fast" mode
        # dash do not really like the "global" objects
        self._is_ok_step_fast = True
        self._curr_step_fast = 0

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
        self.app.callback([dash.dependencies.Output("back_trigger_rt", "n_clicks"),
                           dash.dependencies.Output("back_trigger_for", "n_clicks")],
                          [dash.dependencies.Input("back-button", "n_clicks")],
                          state=[dash.dependencies.State("back_trigger_rt", "n_clicks"),
                                 dash.dependencies.State("back_trigger_for", "n_clicks")]
                          )(self.back_clicked)

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

        # handle the interaction with self.env, that should be done all in one function, otherwise
        # there are concurrency issues
        self.app.callback([dash.dependencies.Output("act_on_env_trigger_rt", "n_clicks"),
                           dash.dependencies.Output("act_on_env_trigger_for", "n_clicks")],
                          [dash.dependencies.Input("step_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("simul_butt_call_act_on_env", "value")]
                          )(self.handle_act_on_env)

        # handle triggers: the collapse of the temporal information
        # TODO do not work now !
        self.app.callback([dash.dependencies.Output("collapsetemp_trigger_temporal_figs", "n_clicks")
                           ],
                          [dash.dependencies.Input('show-temoral-graph', "value")],
                          [dash.dependencies.State("collapsetemp_trigger_temporal_figs", "n_clicks")]
                          )(self.show_tmeporal_graphs)

        # handle triggers: refresh of the figures for real time (graph part)
        self.app.callback([dash.dependencies.Output("figrt_trigger_temporal_figs", "n_clicks"),
                           dash.dependencies.Output("figrt_trigger_rt_graph", "n_clicks"),
                           dash.dependencies.Output("figrt_trigger_for_graph", "n_clicks"),
                           ],
                          [dash.dependencies.Input("act_on_env_trigger_rt", "n_clicks"),
                           dash.dependencies.Input("back_trigger_rt", "n_clicks")],
                          []
                          )(self.update_rt_fig)

        # handle triggers: refresh of the figures for the forecast
        self.app.callback([dash.dependencies.Output("figfor_trigger_for_graph", "n_clicks")],
                          [dash.dependencies.Input("act_on_env_trigger_for", "n_clicks"),
                           # dash.dependencies.Input("simu_trigger_for", "n_clicks"),
                           dash.dependencies.Input("back_trigger_for", "n_clicks")],
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

        # old ugly callbacks

        # # reset has been called
        # self.app.callback([dash.dependencies.Output("dummy-for-reset-hidden", "children")],
        #                   [dash.dependencies.Input('reset-button', 'n_clicks')])(self.has_reset)
        #
        # # callback for the "continue" button
        # self.app.callback([dash.dependencies.Output("step-button", "className"),
        #                    dash.dependencies.Output("simulate-button", "className"),
        #                    dash.dependencies.Output("back-button", "className"),
        #                    dash.dependencies.Output("reset-button", "className"),
        #                    dash.dependencies.Output("continue_til_go-button", "className"),
        #                    dash.dependencies.Output("step-button", "n_clicks"),  # callback to call the "plot function"
        #                    # dash.dependencies.Output("continue_til_go-button", "n_clicks")
        #                    ],
        #                   [dash.dependencies.Input('interval-component', 'n_intervals'),
        #                    dash.dependencies.Input("continue_til_go-button", "n_clicks"),
        #                    dash.dependencies.Input("go_fast-button", "n_clicks"),],
        #                   [
        #                    dash.dependencies.State("step-button", "n_clicks")
        #                   ]
        #                   )(self.advance_time)

        # Register controls update callback (unit information, step and simulate)
        # self.app.callback([dash.dependencies.Output("real-time-graph", "figure"),
        #                    dash.dependencies.Output("simulated-graph", "figure"),
        #                    dash.dependencies.Output("rt_date_time", "children"),
        #                    dash.dependencies.Output("forecast_date_time", "children"),
        #                    dash.dependencies.Output("graph_gen_load", "figure"),
        #                    dash.dependencies.Output("graph_flow_cap", "figure"),
        #                    ],
        #                    [dash.dependencies.Input("step-button", "n_clicks"),
        #                     dash.dependencies.Input("simulate-button", "n_clicks"),
        #                     dash.dependencies.Input("back-button", "n_clicks"),
        #                     dash.dependencies.Input("line-info-dropdown", "value"),
        #                     dash.dependencies.Input("line-side-dropdown", "value"),
        #                     dash.dependencies.Input("load-info-dropdown", "value"),
        #                     dash.dependencies.Input("gen-info-dropdown", "value"),
        #                     dash.dependencies.Input("stor-info-dropdown", "value")
        #                    ],
        #                   )(self.controlTriggers)

        # register callbacks for when a data is clicked on
        # self.app.callback([dash.dependencies.Output("generator_clicked", "style"),
        #                    dash.dependencies.Output("gen-id-hidden", "children"),
        #                    dash.dependencies.Output("gen-id-clicked", "children"),
        #                    dash.dependencies.Output("gen-dispatch", "min"),
        #                    dash.dependencies.Output("gen-dispatch", "max"),
        #                    dash.dependencies.Output("gen-dispatch", "value"),
        #                    dash.dependencies.Output("gen_p", "children"),
        #                    dash.dependencies.Output("target_disp", "children"),
        #                    dash.dependencies.Output("actual_disp", "children"),
        #
        #                    dash.dependencies.Output("storage_clicked", "style"),
        #                    dash.dependencies.Output("storage-id-hidden", "children"),
        #                    dash.dependencies.Output("stor-id-clicked", "children"),
        #                    dash.dependencies.Output("storage-power-input", "min"),
        #                    dash.dependencies.Output("storage-power-input", "max"),
        #                    dash.dependencies.Output("storage-power-input", "value"),
        #                    dash.dependencies.Output("storage_p", "children"),
        #                    dash.dependencies.Output("storage_energy", "children"),
        #
        #                    dash.dependencies.Output("line_clicked", "style"),
        #                    dash.dependencies.Output("line-id-hidden", "children"),
        #                    dash.dependencies.Output("line-id-clicked", "children"),
        #                    dash.dependencies.Output("line-status-input", "value"),
        #                    dash.dependencies.Output("line_flow", "children"),
        #                    ],
        #                   [dash.dependencies.Input("real-time-graph", "clickData"),
        #                    # dash.dependencies.Input("step", "n_clicks"),
        #                    # dash.dependencies.Input("simulate", "n_clicks"),
        #                    ])(self.display_click_data)
        #
        # # print the current action
        # self.app.callback([dash.dependencies.Output("current_action", "children"),
        #                    ],
        #                   [
        #                     # dash.dependencies.Input("step", "n_clicks"),
        #                     # dash.dependencies.Input("simulate", "n_clicks"),
        #                     dash.dependencies.Input("gen-id-hidden", "children"),
        #                     dash.dependencies.Input('gen-dispatch', "value"),
        #                     dash.dependencies.Input("storage-id-hidden", "children"),
        #                     dash.dependencies.Input('storage-power-input', "value"),
        #                     dash.dependencies.Input("line-id-hidden", "children"),
        #                     dash.dependencies.Input('line-status-input', "value"),
        #                   ])(self.display_action)
        #

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
                                     id="continue_til_go-button",
                                     n_clicks=0,
                                     className="btn btn-primary")
        go_fast = html.Label("Fast",
                             id="go_fast-button",
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
                               style={'display': 'none'}  # TODO that do not work for now
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
        layout_click = html.Div([generator_clicked,
                                 storage_clicked,
                                 line_clicked],
                                className='six columns')

        interaction_and_action = html.Div([html.Br(),
                                           layout_click,
                                           action_col], className="row")

        interval_object = dcc.Interval(id='interval-component',
                                       interval=self.time_refresh * 1000,  # in milliseconds
                                       n_intervals=0
                                       )

        # hidden control button, hack for having same output for multiple callbacks
        step_trigger_rt = html.Label("",
                                     id="step_trigger_rt",
                                     n_clicks=0)
        step_trigger_for = html.Label("",
                                      id="step_trigger_for",
                                      n_clicks=0)
        simu_trigger_for = html.Label("",
                                      id="simu_trigger_for",
                                      n_clicks=0)
        back_trigger_for = html.Label("",
                                      id="back_trigger_for",
                                      n_clicks=0)
        back_trigger_rt = html.Label("",
                                     id="back_trigger_rt",
                                     n_clicks=0)
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
        act_on_env_trigger_rt = html.Label("",
                                           id="act_on_env_trigger_rt",
                                           n_clicks=0)
        act_on_env_trigger_for = html.Label("",
                                            id="act_on_env_trigger_for",
                                            n_clicks=0)
        hidden_interactions = html.Div([step_trigger_rt, step_trigger_for,
                                        simu_trigger_for,
                                        back_trigger_for, back_trigger_rt,
                                        figrt_trigger_temporal_figs, collapsetemp_trigger_temporal_figs,
                                        unit_trigger_rt_graph, unit_trigger_for_graph, figrt_trigger_for_graph,
                                        figfor_trigger_for_graph, figrt_trigger_rt_graph,
                                        step_butt_call_act_on_env, simul_butt_call_act_on_env,
                                        act_on_env_trigger_rt,
                                        act_on_env_trigger_for
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
                              temporal_graphs,
                              html.Br(),
                              interaction_and_action,
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
            if self.is_continue_mode is False:
                do_step = 1
        else:
            raise dash.exceptions.PreventUpdate
        return [do_step]

    def back_clicked(self, back_clicks, trigger_rt_update, trigger_for_update):
        """handle the interaction for the "back" button"""
        if self.back_clicks < back_clicks:
            # "back" has been clicked
            self.back_clicks = back_clicks
            if self.is_continue_mode is False:
                self.env.back()   # TODO have this in a callback (dash will not attempt to modify it in two process)
                self.update_obs_fig()
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_rt_update, trigger_for_update]

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
    def handle_act_on_env(self, step_butt, simulate_butt):
        """
        dash do not make "synch" callbacks (two callbacks can be called at the same time),
        however, grid2op environments are not "thread safe": accessing them from different "thread"
        "coroutine" "process" is not a good idea.

        This function ensures that all functions related to the manipulation of the environment
        are done sequentially.

        see https://dash.plotly.com/advanced-callbacks, paragraph
        "Prevent Callback Execution Upon Initial Component Render"
        """
        trigger_rt = 0
        trigger_for = 0
        if step_butt is not None and step_butt > 0:
            # step has been called
            self.env.step()
            self.update_obs_fig()
            trigger_rt = 1
            trigger_for = 1
        elif simulate_butt is not None and simulate_butt > 0:
            self.env.simulate()
            self.plot_grids.update_forecat(self.env.sim_obs)
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"
            trigger_rt = 0
            trigger_for = 1
        else:
            raise dash.exceptions.PreventUpdate

        return [trigger_rt, trigger_for]

    # handle the layout
    def update_rt_fig(self, env_act, back_trigger):
        """the real time figures need to be updated"""
        trigger_temporal_figs = 0
        trigger_rt_graph = 0
        trigger_for_graph = 0
        if env_act is not None and env_act > 0:
            trigger_temporal_figs = 1
            trigger_rt_graph = 1
            trigger_for_graph = 1
        return [trigger_temporal_figs, trigger_rt_graph, trigger_for_graph]

    def update_simulated_fig(self, env_act, back_trigger):
        """the simulate figures need to updated"""
        trigger_for_graph = 0
        if env_act is not None and env_act > 0:
            trigger_for_graph = 1
        return [trigger_for_graph]

    def show_tmeporal_graphs(self, show_temporal_graph, trigger_temporal_figs):
        """handles the action that displays (or not) the time series graphs"""
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
        return [display_mode, self.fig_load_gen, self.fig_line_cap]

    def update_rt_graph_figs(self, figrt_trigger, unit_trigger):
        return [self.real_time,  self.rt_datetime]

    def update_for_graph_figs(self, figrt_trigger, figfor_trigger, unit_trigger):
        return [self.forecast, self.for_datetime]

    # auxiliary functions
    def update_obs_fig(self):
        self.plot_grids.update_rt(self.env.obs)
        self.plot_grids.update_forecat(self.env.sim_obs)
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

    # self.plot_temporal.fig_load_gen, self.plot_temporal.fig_line_cap
    ######## old ugly stuff
    def display_action(self,
                       # step_clicks, simulate_clicks,
                       gen_id, redisp,
                       stor_id, storage_p,
                       line_id, line_status):
        """displays the actions (as text)"""
        # TODO handle better the action (this is ugly to handle it from here!)

        # TODO initialize the value to the last seen value for the dispatch, and not the
        # value in the observation

        res = None
        # if self.step_clicks < step_clicks or self.simulate_clicks < simulate_clicks:
        if False:
            # someone clicked on the "step" or "simulate" button
            res = [f"{self.env.current_action}"]
        else:
            if gen_id != "":
                self.env._current_action.redispatch = [(int(gen_id), float(redisp))]
            if stor_id != "":
                self.env._current_action.storage_p = [(int(stor_id), float(storage_p))]
            if line_id != "" and line_status is not None:
                self.env._current_action.line_set_status = [(int(line_id), int(line_status))]
            res = [f"{self.env.current_action}"]
        return res

    def display_click_data(self, clickData):
        fig, obj_type, obj_id, res_type = self.plot_grids.get_object_clicked(clickData)
        style_gen_input = {'display': 'none'}
        gen_id_clicked = ""
        gen_res = ["Generator id", -1., 1., 0., "gen_p", "target_disp", "actual_disp"]  # gen_id, min_redisp_val, max_redisp_val, redisp_val

        style_storage_input = {'display': 'none'}
        storage_id_clicked = ""
        storage_res = ["Storage id", -1., 1., 0., "storage_power", "storage_capaticy"]

        style_line_input = {'display': 'none'}
        line_id_clicked = ""
        line_res = ["line id", 1, "flow"]
        # https://stackoverflow.com/questions/50213761/changing-visibility-of-a-dash-component-by-updating-other-component
        # if self.step_clicks < step_clicks:
        #     # someone clicked on the "step" button
        #     pass
        # if self.simulate_clicks < simulate_clicks:
        #     # someone clicked on the "simulate" button
        #     pass

        if clickData is None or self.is_continue_mode:
            # either i did not click on any data, or i am in the "go mode"
            pass
        elif obj_type == "gen":
            gen_id_clicked = f"{obj_id}"
            style_gen_input = {'display': 'inline-block'}
            gen_res = res_type
        elif obj_type == "stor":
            storage_id_clicked = f"{obj_id}"
            style_storage_input = {'display': 'inline-block'}
            storage_res = res_type
        elif obj_type == "line":
            line_id_clicked = f"{obj_id}"
            style_line_input = {'display': 'inline-block'}
            line_res = res_type
        # return: gen_style, gen_id, min_val, max_val
        return [style_gen_input, gen_id_clicked, *gen_res,
                style_storage_input, storage_id_clicked, *storage_res,
                style_line_input, line_id_clicked, *line_res
                ]

    def advance_time(self, interval, continue_till_go_clicks, go_fast_clicks, step_clicked):
        self.is_continue_mode = False
        self.is_go_fast = False
        button_shape = "btn btn-primary"
        button_reset_shape = "btn btn-primary"
        go_button_shape = button_shape

        if self.continue_clicks < continue_till_go_clicks:
            self.continue_clicks = continue_till_go_clicks

        if self.go_fast_clicks < go_fast_clicks:
            self.go_fast_clicks = go_fast_clicks

        if self.env.is_done:
            # nothing more to do, i am dead
            button_shape = "btn btn-secondary"
            go_button_shape = "btn btn-secondary"
            return [button_shape, button_shape, button_shape, button_reset_shape, go_button_shape]

        # TODO here need to address these "heavy" computation
        # if self._is_ok_step_fast is False:
        #     button_shape = "btn btn-secondary"
        #     go_button_shape = button_shape
        #
        # if self.go_fast_clicks % 2 == 1 and not self.is_go_fast and self._is_ok_step_fast:
        #     # still in the "go_fast" mode
        #     self.is_continue_mode = True
        #     self.is_go_fast = True
        #
        #     self._is_ok_step_fast = False
        #     # weird stuff to prevent dash to call "make_step" twice
        #     for i in range(self.nb_step_gofast):
        #         self.make_step()
        #     self._is_ok_step_fast = True
        #
        #     button_shape = "btn btn-secondary"
        #     go_button_shape = button_shape

        if self.continue_clicks % 2 == 1 and not self.is_go_fast:
            # still in the "advance-time" mode
            self.is_continue_mode = True
            self.make_step()
            button_shape = "btn btn-secondary"
            button_reset_shape = "btn btn-secondary"
            step_clicked += 1  # I plot the graph

        return [button_shape, button_shape, button_shape, button_reset_shape, go_button_shape,
                step_clicked]

    # def has_reset(self, reset_clicks):
    #     if self.is_continue_mode:
    #         # do not reset if in "continue to simulate" mode
    #         return ["toto"]
    #
    #     if self.reset_clicks < reset_clicks:
    #         self.reset_clicks = reset_clicks
    #         self.env.reset()
    #         self.update_obs_fig()
    #     return ["toto"]

    def controlTriggers(self,
                        step_clicks, simulate_clicks, back_clicks,
                        line_unit, line_side, load_unit, gen_unit, stor_unit):
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

        if self.step_clicks < step_clicks:
            # "step" has been clicked
            self.step_clicks = step_clicks
            if self.is_continue_mode is False:
                self.make_step()

        if self.simulate_clicks < simulate_clicks:
            self.simulate_clicks = simulate_clicks
            # simulate has been called
            if self.is_continue_mode is False:
                self.env.simulate()
                self.plot_grids.update_forecat(self.env.sim_obs)
                self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # TODO ugly way to display the date and time ...
        return [self.real_time, self.forecast, self.rt_datetime, self.for_datetime,
                self.plot_temporal.fig_load_gen, self.plot_temporal.fig_line_cap]

    def run(self, debug=False):
        self.app.run_server(debug=debug)
