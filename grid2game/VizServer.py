# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import os
import dash
import time

try:
    # newest version of dash
    from dash import dcc
except ImportError:
    import dash_core_components as dcc
try:
    # newest version of dash
    from dash import html
except ImportError:
    import dash_html_components as html
import dash_bootstrap_components as dbc
from grid2game.plot import PlotGrids
from grid2game.plot import PlotTemporalSeries
from grid2game.envs import Env


class VizServer:
    SELF_LOOP_STOP = 0
    SELF_LOOP_GO = 1
    SELF_LOOP_GOFAST = 2

    def __init__(self,
                 server,
                 args,
                 logger=None,
                 logging_level=None  # only used if logger is None
                 ):
        meta_tags = [
            {
                'name': 'grid2game',
                'content': 'Grid2Game a gamified platform to interact with grid2op environments'
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
            dbc.themes.BOOTSTRAP,
            {
                "rel": "stylesheet",
                "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
                "integrity": "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
                "crossorigin": "anonymous"
            },
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
            os.path.join(os.path.dirname(__file__), "assets")
        )

        if logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
            formatter = logging.Formatter('%(asctime)s - %(name)s %(filename)s.%(lineno)d | '
                                          '%(levelname)s:: %(message)s')
            fh = logging.FileHandler(f'{__name__}.log')
            fh.setFormatter(formatter)
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            if logging_level is not None:
                fh.setLevel(logging_level)
                ch.setLevel(logging_level)
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
        else:
            self.logger = logger.getChild("VizServer")

        # create the dash app
        self.my_app = dash.Dash(__name__,
                                server=server if server is not None else True,
                                meta_tags=meta_tags,
                                assets_folder=assets_dir,
                                external_stylesheets=external_stylesheets,
                                external_scripts=external_scripts)
        self.logger.info("Dash app initialized")
        # self.app.config.suppress_callback_exceptions = True

        # create the grid2op related things
        self.assistant_path = str(args.assistant_path)
        self.save_expe_path = ""
        self.env = Env(args.env_name,
                       test=args.is_test,
                       assistant_path=self.assistant_path,
                       assistant_seed=int(args.assistant_seed) if args.assistant_seed is not None else None,
                       logger=self.logger)
        self.logger.info("Environment initialized")
        self.plot_grids = PlotGrids(self.env.observation_space)
        self.fig_timeline = self.env.get_timeline_figure()

        self.plot_temporal = PlotTemporalSeries(self.env.env_tree)
        self.fig_load_gen = self.plot_temporal.fig_load_gen
        self.fig_line_cap = self.plot_temporal.fig_line_cap

        if args.env_seed is not None:
            self.env.seed(args.env_seed)

        # internal members
        self.step_clicks = 0
        self.simulate_clicks = 0
        self.back_clicks = 0
        self.go_clicks = 1
        self.gofast_clicks = 0
        self.reset_clicks = 0
        self.nb_step_gofast = 12  # number of steps made in each frame for the "go_fast" mode
        # TODO implement the to below
        self.time_refresh = 0.1  # in seconds (time at which the page will be refreshed)
        self.is_previous_click_end = False  # does the previous click on the button is the button
        # that makes it go until the end of the game ? If so i will need to upgrade, at the end of it, the
        # state of the grid

        # remembering the last step, that are not saved in the observation...
        self._last_step = 0
        self._last_max_step = 1
        self._last_done = False

        # buttons layout
        self._button_shape = "btn btn-primary"
        self._go_button_shape = "btn btn-primary"
        self._gofast_button_shape = "btn btn-primary"

        # ugly hack for the date time display
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # tools to plot
        self.plot_grids.init_figs(self.env.obs, self.env.sim_obs)
        self.real_time = self.plot_grids.figure_rt
        self.forecast = self.plot_grids.figure_forecat

        # initialize the layout
        self.my_app.layout = self.setupLayout()

        # handle the press to one of the button to change the units
        self.my_app.callback([dash.dependencies.Output("unit_trigger_rt_graph", "n_clicks"),
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
        self.my_app.callback([dash.dependencies.Output("do_display_action", "value"),

                              dash.dependencies.Output("generator_clicked", "style"),
                              dash.dependencies.Output("gen-redisp-curtail", "children"),
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
                              dash.dependencies.Input("go_till_game_over-button", "n_clicks"),
                              ]
                             )(self.display_click_data)

        # handle display of the action, if needed
        self.my_app.callback([dash.dependencies.Output("current_action", "children"),
                              ],
                             [dash.dependencies.Input("which_action_button", "value"),
                              dash.dependencies.Input("do_display_action", "value"),
                              dash.dependencies.Input("gen-redisp-curtail", "children"),
                              dash.dependencies.Input("gen-id-hidden", "children"),
                              dash.dependencies.Input('gen-dispatch', "value"),
                              dash.dependencies.Input("storage-id-hidden", "children"),
                              dash.dependencies.Input('storage-power-input', "value"),
                              dash.dependencies.Input("line-id-hidden", "children"),
                              dash.dependencies.Input('line-status-input', "value"),
                              dash.dependencies.Input('sub-id-hidden', "children"),
                              dash.dependencies.Input("graph_clicked_sub", "clickData")
                              ])(self.display_action_fun)

        # handle the interaction with self.env, that should be done all in one function, otherwise
        # there are concurrency issues
        self.my_app.callback([
            # trigger the computation if needed
            dash.dependencies.Output("trigger_computation", "value"),
            # update the button color / shape / etc. if needed
            dash.dependencies.Output("step-button", "className"),
            dash.dependencies.Output("simulate-button", "className"),
            dash.dependencies.Output("back-button", "className"),
            dash.dependencies.Output("reset-button", "className"),
            dash.dependencies.Output("go-button", "className"),
            dash.dependencies.Output("gofast-button", "className"),
                           ],
                          [dash.dependencies.Input("step-button", "n_clicks"),
                           dash.dependencies.Input("simulate-button", "n_clicks"),
                           dash.dependencies.Input("back-button", "n_clicks"),
                           dash.dependencies.Input("reset-button", "n_clicks"),
                           dash.dependencies.Input("go-button", "n_clicks"),
                           dash.dependencies.Input("gofast-button", "n_clicks"),
                           dash.dependencies.Input("go_till_game_over-button", "n_clicks"),
                           dash.dependencies.Input("untilgo_butt_call_act_on_env", "value"),
                           dash.dependencies.Input("selfloop_call_act_on_env", "value"),
                           dash.dependencies.Input("timer", "n_intervals")
                           ],
                          [dash.dependencies.State("act_on_env_trigger_rt", "n_clicks"),
                           dash.dependencies.State("act_on_env_trigger_for", "n_clicks"),
                           dash.dependencies.State("act_on_env_call_selfloop", "value")]
                          )(self.handle_act_on_env)

        self.my_app.callback([dash.dependencies.Output("act_on_env_trigger_rt", "n_clicks"),
                              dash.dependencies.Output("act_on_env_trigger_for", "n_clicks")],
                             [dash.dependencies.Input("trigger_computation", "value"),
                              dash.dependencies.Input("recompute_rt_from_timeline", "n_clicks")]
                             )(self.computation_wrapper)

        # handle triggers: refresh of the figures for real time (graph part)
        self.my_app.callback([dash.dependencies.Output("figrt_trigger_temporal_figs", "n_clicks"),
                              dash.dependencies.Output("figrt_trigger_rt_graph", "n_clicks"),
                              dash.dependencies.Output("figrt_trigger_for_graph", "n_clicks"),
                              dash.dependencies.Output("scenario_progression", "value"),
                              dash.dependencies.Output("scenario_progression", "children"),
                              dash.dependencies.Output("scenario_progression", "color"),
                              dash.dependencies.Output("timeline_graph", "figure"),
                              ],
                             [dash.dependencies.Input("act_on_env_trigger_rt", "n_clicks")],
                             []
                             )(self.update_rt_fig)

        # handle triggers: refresh of the figures for the forecast
        self.my_app.callback([dash.dependencies.Output("figfor_trigger_for_graph", "n_clicks")],
                             [dash.dependencies.Input("act_on_env_trigger_for", "n_clicks"),
                              ],
                             []
                             )(self.update_simulated_fig)

        # final graph display
        # handle triggers: refresh the figures (temporal series part)
        self.my_app.callback([
                           dash.dependencies.Output("graph_gen_load", "figure"),
                           dash.dependencies.Output("graph_flow_cap", "figure"),
                           ],
                          [dash.dependencies.Input("figrt_trigger_temporal_figs", "n_clicks"),
                           dash.dependencies.Input("showtempo_trigger_rt_graph", "n_clicks")
                           ],
                          )(self.update_temporal_figs)

        # self.my_app.callback([dash.dependencies.Output('temporal_graphs', "style"),
        #                    dash.dependencies.Output("showtempo_trigger_rt_graph", "n_clicks")
        #                    ],
        #                   [dash.dependencies.Input('show-temporal-graph', "value")]
        #                   )(self.show_hide_tempo_graph)

        # handle final graph of the real time grid
        self.my_app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                              dash.dependencies.Output("rt_date_time", "children")],
                             [dash.dependencies.Input("figrt_trigger_rt_graph", "n_clicks"),
                              dash.dependencies.Input("unit_trigger_rt_graph", "n_clicks"),
                              ]
                             )(self.update_rt_graph_figs)

        # handle final graph for the forecast grid
        self.my_app.callback([dash.dependencies.Output("simulated-graph", "figure"),
                              dash.dependencies.Output("forecast_date_time", "children")],
                             [dash.dependencies.Input("figrt_trigger_for_graph", "n_clicks"),
                              dash.dependencies.Input("figfor_trigger_for_graph", "n_clicks"),
                              dash.dependencies.Input("unit_trigger_for_graph", "n_clicks"),
                              ]
                             )(self.update_for_graph_figs)

        # load the assistant
        self.my_app.callback([dash.dependencies.Output("current_assistant_path", "children"),
                              dash.dependencies.Output("clear_assistant_path", "n_clicks")],
                             [dash.dependencies.Input("load_assistant_button", "n_clicks")],
                             [dash.dependencies.State("select_assistant", "value")]
                             )(self.load_assistant)

        self.my_app.callback([dash.dependencies.Output("select_assistant", "value")],
                             [dash.dependencies.Input("clear_assistant_path", "n_clicks")]
                             )(self.clear_loading)

        self.my_app.callback([dash.dependencies.Output("current_save_path", "children")],
                             [dash.dependencies.Input("save_expe_button", "n_clicks")],
                             [dash.dependencies.State("save_expe", "value")]
                             )(self.save_expe)

        # callback for the timeline
        self.my_app.callback([dash.dependencies.Output("recompute_rt_from_timeline", "n_clicks")],
                             [dash.dependencies.Input('timeline_graph', 'clickData')])(self.timeline_set_time)
        self.logger.info("Viz server initialized")

    def run_server(self, debug=False):
        self.my_app.run_server(debug=debug)

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

        # Controls widget (step, reset etc.)
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
        go_butt = html.Label("Go",
                             id="go-button",
                             n_clicks=0,
                             className="btn btn-primary")
        go_fast = html.Label("+1h",
                             id="gofast-button",
                             n_clicks=0,
                             className="btn btn-primary",
                             # style={'display': 'none'}
                             )
        go_till_game_over = html.Label("End",
                                       id="go_till_game_over-button",
                                       n_clicks=0,
                                       className="btn btn-primary",
                                       # style={'display': 'none'}
                                       )
        # html display
        button_css = "col-6 col-sm-6 col-md-3 col-lg-3 col-xl-1"
        reset_col = html.Div(id="reset-col", className=button_css, children=[reset_button, reset_button_dummy])
        step_col = html.Div(id="step-col", className=button_css, children=[step_button])
        sim_col = html.Div(id="sim-step-col", className=button_css, children=[simulate_button])
        back_col = html.Div(id="back-col", className=button_css, children=[back_button])
        go_col = html.Div(id="go-col", className=button_css, children=[go_butt])
        go_fast_col = html.Div(id="go_fast-col", className=button_css, children=[go_fast])
        go_till_game_over_col = html.Div(id="continue_until_game_over-col",
                                         className=button_css,
                                         children=[go_till_game_over])

        # Units displayed control
        # TODO add a button "trust assistant up to" that will play the actions suggested by the
        # TODO assistant
        show_temporal_graph = dcc.Checklist(id="show-temporal-graph",
                                            options=[{'label': 'TODO Display time series', 'value': '1'}],
                                            value=["1"]
                                            )

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
                                 ], value='none', clearable=False)

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
                                 value='none',
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
                                value='none',
                                clearable=False)

        stor_info_label = html.Label("Stor. unit:")
        stor_info = dcc.Dropdown(id='stor-info-dropdown',
                                 options=[
                                     {'label': 'MW', 'value': 'p'},
                                     {'label': 'MWh', 'value': 'MWh'},
                                     {'label': 'None', 'value': 'none'},
                                 ],
                                 value='none',
                                 clearable=False)
        lineinfo_col = html.Div(id="lineinfo-col", className=button_css, children=[line_info_label, line_info])
        lineside_col = html.Div(id="lineside-col", className=button_css, children=[line_side_label, line_side])
        loadinfo_col = html.Div(id="loadinfo-col", className=button_css, children=[load_info_div])
        geninfo_col = html.Div(id="geninfo-col", className=button_css, children=[gen_info_label, gen_info])
        storinfo_col = html.Div(id="storinfo-col", className=button_css, children=[stor_info_label, stor_info])
        # storinfo_col = html.Div(id="storinfo-col", className=button_css, children=[stor_info_label,
        # show_temporal_graph])

        # general layout
        change_units = html.Div(id="change_units",
                                children=[
                                    lineinfo_col,
                                    lineside_col,
                                    loadinfo_col,
                                    geninfo_col,
                                    storinfo_col,
                                    # show_temporal_graph
                                ],
                                className="row",
                                )

        controls_row = html.Div(id="control-buttons",
                                className="row",
                                children=[
                                    back_col,  # TODO display back only if its possible in the self.env
                                    step_col,
                                    sim_col,
                                    go_col,
                                    go_fast_col,
                                    go_till_game_over_col
                                ])
        select_assistant = html.Div(id='select_assistant_box',
                                    children=html.Div([dcc.Input(placeholder='Copy paste assistant location',
                                                                 id="select_assistant",
                                                                 type="text",
                                                                 style={
                                                                     'width': '68%',
                                                                     'height': '55px',
                                                                     'lineHeight': '55px',
                                                                     'vertical-align': 'middle',
                                                                     "margin-top": 5,
                                                                     "margin-left": 20}),
                                                       html.Label("load",
                                                                  id="load_assistant_button",
                                                                  n_clicks=0,
                                                                  className="btn btn-primary",
                                                                  style={'height': '35px',
                                                                         "margin-top": 18,
                                                                         "margin-left": 5}),
                                                       html.P(self.format_path(self.assistant_path),
                                                              id="current_assistant_path",
                                                              style={'width': '24%',
                                                                     'textAlign': 'center',
                                                                     'height': '55px',
                                                                     'vertical-align': 'middle',
                                                                     "margin-top": 20}
                                                              ),
                                                       ],
                                                      className="row",
                                                      style={'height': '65px', 'width': '100%'},
                                                      ),
                                    style={
                                          'borderWidth': '1px',
                                          'borderStyle': 'dashed',
                                          'borderRadius': '5px',
                                          'textAlign': 'center',
                                          'margin': '10px'
                                    }
                                    )
        save_experiment = html.Div(id='save_expe_box',
                                   children=html.Div([dcc.Input(placeholder='Where do you want to save the current '
                                                                            'experiment?',
                                                                id="save_expe",
                                                                type="text",
                                                                style={
                                                                    'width': '68%',
                                                                    'height': '55px',
                                                                    'lineHeight': '55px',
                                                                    'vertical-align': 'middle',
                                                                    "margin-top": 5,
                                                                    "margin-left": 20}),
                                                      html.Label("save",
                                                                 id="save_expe_button",
                                                                 n_clicks=0,
                                                                 className="btn btn-primary",
                                                                 style={'height': '35px',
                                                                        "margin-top": 18,
                                                                        "margin-left": 5}),
                                                      html.P(self.format_path(self.assistant_path),
                                                             id="current_save_path",
                                                             style={'width': '24%',
                                                                    'textAlign': 'center',
                                                                    'height': '55px',
                                                                    'vertical-align': 'middle',
                                                                    "margin-top": 20}
                                                             ),
                                                      ],
                                                     className="row",
                                                     style={'height': '65px', 'width': '100%'},
                                                     ),
                                   style={
                                         'borderWidth': '1px',
                                         'borderStyle': 'dashed',
                                         'borderRadius': '5px',
                                         'textAlign': 'center',
                                         'margin': '10px'
                                   }
                                   )
        controls_row = html.Div(id="controls-row",
                                children=[
                                    reset_col,
                                    controls_row,
                                    select_assistant,
                                    save_experiment,
                                    change_units
                                ])

        # progress in the scenario (progress bar and timeline)
        progress_bar_for_scenario = html.Div(children=[html.Div(dbc.Progress(id="scenario_progression",
                                                                             value=0.,
                                                                             color="danger"),
                                                                ),
                                                       html.Div(dcc.Graph(id="timeline_graph",
                                                                          config={
                                                                              # 'displayModeBar': False,
                                                                              "responsive": True,
                                                                              # "autosizable": True
                                                                              },
                                                                          figure=self.fig_timeline,
                                                                          style={"height": '10vh'}
                                                                          ),

                                                                ),
                                                       html.Br(),
                                                       ],
                                             className="six columns",
                                             # style={'width': '100%', "height": "300px"}
                                             )

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
        rt_date_time = html.P(self.rt_datetime, style={'text-align': 'center'}, id="rt_date_time")
        rt_graph_div = html.Div(id="rt_graph_div",
                                className=graph_css,
                                children=[
                                    rt_graph_label,
                                    rt_date_time,
                                    real_time_graph],
                                style={'display': 'inline-block',
                                       'width': '50%',
                                       }
                                )
        forecast_graph_label = html.H3("Forecast (t+5mins):", style={'text-align': 'center'})
        forecast_date_time = html.P(self.for_datetime, style={'text-align': 'center'}, id="forecast_date_time")
        sim_graph_div = html.Div(id="sim_graph_div",
                                 className=graph_css,
                                 children=[
                                     forecast_graph_label,
                                     forecast_date_time,
                                     simulate_graph],

                                 style={'display': 'inline-block',
                                        'width': '50%',
                                        }
                                 )

        graph_col = html.Div(id="graph-col",
                             children=[
                                 html.Br(),
                                 rt_graph_div,
                                 sim_graph_div
                             ],
                             className="row",
                             style={'width': '100%', 'height': '55vh'},
                             # style={'display': 'inline-block'}  # to allow stacking next to each other
                             )

        ## Grid state widget
        row_css = "row d-xl-flex flex-xl-grow-1"
        state_row = html.Div(id="state-row",
                             # className="row",
                             children=[graph_col]
                             )

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
                                                    'width': '50%', 'height': '47vh'}),
                                    html.Div([graph_flow_cap],
                                             className=graph_css,
                                             style={'display': 'inline-block',
                                                    'width': '50%', 'height': '47vh'})
                                    ],
                                   style={'width': '100%'},
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
        which_action_button = dcc.Dropdown(id='which_action_button',
                                           options=[
                                               {'label': 'do nothing', 'value': 'dn'},
                                               {'label': 'previous', 'value': 'prev'},
                                               {'label': 'assistant', 'value': 'assistant'},
                                           ],
                                           value='assistant',
                                           clearable=False)
        action_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-5 " \
                     "order-first order-sm-first order-md-first order-xl-last"
        action_css = "six columns"
        styles = {
            'pre': {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }
        }
        # interactive action panel
        generator_clicked = html.Div([html.P("Generator id", id="gen-id-clicked"),
                                      html.P("Redispatching / curtailment:", id="gen-redisp-curtail"),
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
                                              # 'displayModeBar': False,
                                              # "responsive": True,
                                              # "autosizable": False
                                          },
                                          style={
                                                 # 'width': '100%',
                                                 # 'height': '47vh'
                                                 }
                                          ),
                                html.P("",
                                       id="sub-id-hidden",
                                       style={'display': 'none'}
                                       )
                                ],
                               id="sub_clicked",
                               className="six columns",
                               style={'display': 'inline-block',
                                      'width': '100%',
                                      }
                               )
        layout_click = html.Div([generator_clicked,
                                 storage_clicked,
                                 line_clicked,
                                 sub_clicked],
                                className='six columns',
                                style={"width": "60%",
                                       'display': 'inline-block'})

        # print (str) the action
        action_widget_title = html.Div(id="action_widget_title",
                                       children=[html.P("Action:  "),
                                                 which_action_button],
                                       style={'width': '100%'},
                                       )
        action_col = html.Div(id="action_widget",
                              className=action_css,
                              children=[current_action],
                              style={'display': 'inline-block', 'width': '40%'}
                              )
        
        # combine both
        interaction_and_action = html.Div([html.Br(),
                                           action_widget_title,
                                           html.Div([layout_click,
                                                     action_col],
                                                    className="row",
                                                    style={"width": "100%"},
                                                    )
                                           ])

        # hidden control button, hack for having same output for multiple callbacks
        interval_object = dcc.Interval(id='interval-component',
                                       interval=self.time_refresh * 1000,  # in milliseconds
                                       n_intervals=0
                                       )
        figrt_trigger_temporal_figs = html.Label("",
                                                 id="figrt_trigger_temporal_figs",
                                                 n_clicks=0)
        # collapsetemp_trigger_temporal_figs = html.Label("",
        #                                                 id="collapsetemp_trigger_temporal_figs",
        #                                                 n_clicks=0)
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

        showtempo_trigger_rt_graph = html.Label("",
                                                id="showtempo_trigger_rt_graph",
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
        untilgo_butt_call_act_on_env = dcc.Input(placeholder=" ",
                                                 id='untilgo_butt_call_act_on_env',
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
        trigger_computation = dcc.Input(placeholder=" ",
                                        id='trigger_computation',
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
        clear_assistant_path = html.Label("",
                                          id="clear_assistant_path",
                                          n_clicks=0)
        recompute_rt_from_timeline = html.Label("",
                                                id="recompute_rt_from_timeline",
                                                n_clicks=0)
        hidden_interactions = html.Div([figrt_trigger_temporal_figs,
                                        unit_trigger_rt_graph, unit_trigger_for_graph, figrt_trigger_for_graph,
                                        figfor_trigger_for_graph, figrt_trigger_rt_graph,
                                        showtempo_trigger_rt_graph,
                                        step_butt_call_act_on_env, simul_butt_call_act_on_env,
                                        back_butt_call_act_on_env, go_butt_call_act_on_env,
                                        gofast_butt_call_act_on_env,
                                        untilgo_butt_call_act_on_env,
                                        act_on_env_trigger_rt,
                                        act_on_env_trigger_for, reset_butt_call_act_on_env,
                                        act_on_env_call_selfloop, selfloop_call_act_on_env,
                                        do_display_action, clear_assistant_path,
                                        trigger_computation, recompute_rt_from_timeline
                                        ],
                                       id="hidden_button_for_callbacks",
                                       style={'display': 'none'})

        # timer for the automatic callbacks
        timer_callbacks = dcc.Interval(id="timer",
                                       interval=500.  # in ms
                                       )

        # Final page
        layout_css = "container-fluid h-100 d-md-flex d-xl-flex flex-md-column flex-xl-column"
        layout = html.Div(id="grid2game",
                          className=layout_css,
                          children=[
                              header,
                              html.Br(),
                              controls_row,
                              html.Br(),
                              progress_bar_for_scenario,
                              html.Br(),
                              html.Div([html.P("")], className="six columns"),
                              state_row,  # the two graphs of the grid
                              html.Div([html.P("")], style={"height": "10uv"}),
                              html.Br(),
                              interaction_and_action,
                              html.Br(),
                              temporal_graphs,
                              interval_object,
                              hidden_interactions,
                              timer_callbacks
                          ])

        return layout

    def unit_clicked(self, line_unit, line_side, load_unit, gen_unit, stor_unit,
                     trigger_rt_graph, trigger_for_graph):
        """handle the click to all button to change the units"""
        trigger_rt_graph = 0
        trigger_for_graph = 0
        # controls the panels of the main graph of the grid
        if line_unit != self.plot_grids.line_info:
            self.plot_grids.line_info = line_unit
            self.plot_grids.update_lines_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if line_side != self.plot_grids.line_side:
            self.plot_grids.line_side = line_side
            self.plot_grids.update_lines_side()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if load_unit != self.plot_grids.load_info:
            self.plot_grids.load_info = load_unit
            self.plot_grids.update_loads_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if gen_unit != self.plot_grids.gen_info:
            self.plot_grids.gen_info = gen_unit
            self.plot_grids.update_gens_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if stor_unit != self.plot_grids.storage_info:
            self.plot_grids.storage_info = stor_unit
            self.plot_grids.update_storages_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        return [trigger_rt_graph, trigger_for_graph]

    # handle the interaction with the grid2op environment
    def handle_act_on_env(self,
                          step_butt,
                          simulate_butt,
                          back_butt,
                          reset_butt,
                          go_butt,
                          gofast_clicks,
                          until_game_over,
                          untilgo_butt,
                          self_loop,
                          state_trigger_rt,
                          state_trigger_for,
                          state_trigger_self_loop,
                          timer):
        """
        dash do not make "synch" callbacks (two callbacks can be called at the same time),
        however, grid2op environments are not "thread safe": accessing them from different "thread"
        "coroutine" "process" is not a good idea.

        This function ensures that all functions related to the manipulation of the environment
        are done sequentially.

        see https://dash.plotly.com/advanced-callbacks, paragraph
        "Prevent Callback Execution Upon Initial Component Render"
        """
        # check which call backs triggered this calls
        # see https://dash.plotly.com/advanced-callbacks
        # section "Determining which Input has fired with dash.callback_context"
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            raise dash.exceptions.PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        trigger_heavy_computation_wrapper = 1
        something_clicked = True

        # now register the next computation to do, based on the button triggerd
        if button_id == "step-button":
            self.env.start_computation()
            self.env.next_computation = "step"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = False
        elif button_id == "go_till_game_over-button":
            self.env.start_computation()
            self.env.next_computation = "step_end"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = True
            # self._button_shape = "btn btn-secondary"
            # self._go_button_shape = "btn btn-secondary"
        elif button_id == "reset-button":
            self.env.start_computation()
            self.env.next_computation = "reset"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = False
        elif button_id == "simulate-button":
            self.env.start_computation()
            self.env.next_computation = "simulate"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = False
        elif button_id == "back-button":
            self.env.start_computation()
            self.env.next_computation = "back"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = False
        elif button_id == "gofast-button":
            # this button is off now !
            self.env.start_computation()
            self.env.next_computation = "step_rec_fast"
            self.env.next_computation_kwargs = {"nb_step_gofast": self.nb_step_gofast}
        elif button_id == "go-button":
            self.go_clicks += 1
            if self.go_clicks % 2:
                # i clicked on gofast an even number of time, i need to stop computation
                self.env.stop_computation()
                self._button_shape = "btn btn-primary"
                self._gofast_button_shape = "btn btn-primary"
            else:
                # i clicked on gofast an even number of time, i need to stop computation
                self.env.start_computation()
                self._button_shape = "btn btn-secondary"
                self._gofast_button_shape = "btn btn-secondary"
            self.env.next_computation = "step_rec"
            self.env.next_computation_kwargs = {}
            self.is_previous_click_end = False
        else:
            something_clicked = False

        if not self.env.needs_compute():
            # don't start the computation if not needed
            trigger_heavy_computation_wrapper = dash.no_update

        if not self.env.needs_compute() and self.is_previous_click_end and not something_clicked:
            # in this case, this should be the first call to this function after the "operate the grid until the
            # end" function is called
            # so i need to force update the figures
            trigger_heavy_computation_wrapper = 1
            self.is_previous_click_end = False
            # I need that to the proper update of the progress bar
            self._last_step = self.env.obs.current_step
            self._last_max_step = self.env.obs.max_step

        return [trigger_heavy_computation_wrapper,
                self._button_shape,
                self._button_shape,
                self._button_shape,
                self._button_shape,
                self._go_button_shape,
                self._gofast_button_shape]

    def computation_wrapper(self, trigger_heavy_computation_wrapper, recompute_rt_from_timeline):
        # simulate a "state" of the application that depends on the computation
        if not self.env.is_computing():
            self.env.heavy_compute()
        # TODO the condition to update the stuff
        # TODO and better yet: use the no_update !
        trigger_rt = 1
        trigger_for = 1
        return [trigger_rt, trigger_for]

    # handle the layout
    def update_rt_fig(self, env_act):
        """the real time figures need to be updated"""
        if env_act is not None and env_act > 0:
            self.update_obs_fig()
            trigger_temporal_figs = 1
            trigger_rt_graph = 1
            trigger_for_graph = 1

            # scenario progress bar
            progress_color = None
            if not self.env.is_done:
                self._last_step = self.env.obs.current_step
                self._last_max_step = self.env.obs.max_step
                self._last_done = False
            else:
                if not self._last_done:
                    self._last_done = True
                    if self._last_step != self._last_max_step:
                        # fail to run the scenario till the end
                        self._last_step += 1
                if self._last_step != self._last_max_step:
                    # fail to run the scenario till the end
                    progress_color = "danger"
                else:
                    # no game over, until the end of the scenario
                    progress_color = "success"

            progress_pct = 100. * self._last_step / self._last_max_step
            progress_label = f"{self._last_step} / {self._last_max_step}"
        else:
            raise dash.exceptions.PreventUpdate
        if trigger_rt_graph == 1:
            self.fig_timeline = self.env.get_timeline_figure()
        return [trigger_temporal_figs,
                trigger_rt_graph,
                trigger_for_graph,
                progress_pct,
                progress_label,
                progress_color,
                self.fig_timeline]

    def update_simulated_fig(self, env_act):
        """the simulate figures need to updated"""
        if env_act is not None and env_act > 0:
            trigger_for_graph = 1
            self.plot_grids.update_forecat(self.env.sim_obs, self.env)
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_for_graph]

    def show_temporal_graphs(self, show_temporal_graph):
        """handles the action that displays (or not) the time series graphs"""
        if (show_temporal_graph is None or show_temporal_graph.empty()):
            raise dash.exceptions.PreventUpdate
        return [1]

    # define the style of the temporal graph, whether is how it or not
    def show_hide_tempo_graph(self, do_i_show):
        display_mode = {'display': 'none'}
        if do_i_show:
            # i should display the figure
            display_mode = {'display': 'block'}
            self.plot_temporal.update_layout_height()  # otherwise figures shrink when trigger is called
        return [display_mode, 1]

    # end point of the trigger stuff: what is displayed on the page !
    def update_temporal_figs(self, figrt_trigger, showhide_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (showhide_trigger is None or showhide_trigger == 0):
            raise dash.exceptions.PreventUpdate
        self.fig_load_gen, self.fig_line_cap = self.plot_temporal.update_trace(self.env, self.env.env_tree)
        return [self.fig_load_gen, self.fig_line_cap]

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
        self.plot_grids.update_rt(self.env.obs, self.env)
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.plot_grids.update_forecat(self.env.sim_obs, self.env)
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

    def display_action_fun(self,
                           which_action_button,
                           do_display,
                           gen_redisp_curtail,
                           gen_id,
                           redisp,
                           stor_id, storage_p,
                           line_id, line_status,
                           sub_id, clicked_sub_fig):
        """
        modify the action taken based on the inputs,
        then displays the action (as text)
        """
        # TODO handle better the action (this is ugly to access self.env._current_action from here)

        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            # return [""]
            return [f"{self.env.current_action}"]
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == "which_action_button":
            # the "base action" has been modified, so i need to change it here
            if which_action_button == "dn":
                self.env.next_action_is_dn()
            elif which_action_button == "assistant":
                self.env.next_action_is_assistant()
            elif which_action_button == "prev":
                self.env.next_action_is_previous()
            else:
                # nothing is done
                pass
            res = [f"{self.env.current_action}"]
        elif not do_display:
            # i should not display the action
            # res = [""]
            res = [f"{self.env.current_action}"]
        else:
            # i need to display the action
            self.env.next_action_is_manual()
            is_modif = False
            if gen_id != "":
                try:
                    gen_id_int = int(gen_id)
                    if self.env.glop_env.gen_renewable[gen_id_int]:
                        self.env._current_action.curtail_mw = [(int(gen_id), float(redisp))]

                    else:
                        self.env._current_action.redispatch = [(int(gen_id), float(redisp))]
                    is_modif = True
                except Exception as exc_:
                    # either initialization of something else
                    self.logger.error(f"Error in display_action_fun: {exc_}")
                    pass
            if stor_id != "":
                self.env._current_action.storage_p = [(int(stor_id), float(storage_p))]
                is_modif = True
            if line_id != "" and line_status is not None:
                self.env._current_action.line_set_status = [(int(line_id), int(line_status))]
                is_modif = True
            if sub_id != "":
                is_modif = True
                if clicked_sub_fig is not None:
                    # i modified a substation topology
                    obj_id, new_bus = self.plot_grids.get_object_clicked_sub(clicked_sub_fig)
                    if obj_id is not None:
                        self.env._current_action.set_bus = [(obj_id, new_bus)]

            if not is_modif:
                raise dash.exceptions.PreventUpdate
            # else:
            #     # i force the env to do the "current_action" in the next step
            #     self.env.next_action_from = self.env.LIKE_PREVIOUS

            # TODO optim here to save that if not needed because nothing has changed
            res = [f"{self.env.current_action}"]
        return res

    def display_click_data(self,
                           clickData,
                           back_clicked,
                           step_clicked,
                           simulate_clicked,
                           go_clicked,
                           gofast_clicked,
                           until_gameover):
        """display the interaction window when the real time graph is clicked on"""
        do_display_action = 0
        gen_redisp_curtail = ""
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
                    style_gen_input, gen_redisp_curtail, gen_id_clicked, *gen_res,
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
                gen_redisp_curtail = "Curtail (MW)" if self.env.glop_env.gen_renewable[obj_id] else "Redispatch"
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
                style_gen_input, gen_redisp_curtail, gen_id_clicked, *gen_res,
                style_storage_input, storage_id_clicked, *storage_res,
                style_line_input, line_id_clicked, *line_res,
                style_sub_input, sub_id_clicked, *sub_res
                ]

    def format_path(self, path):
        """just output the name of the submission instead of its whole path"""
        try:
            base, res = os.path.split(path)
            return res.strip()
        except Exception as exc_:
            return path

    def load_assistant(self, trigger_load, assistant_path):
        """loads an assistant and display the right things"""
        if assistant_path is None:
            raise dash.exceptions.PreventUpdate
        self.assistant_path = assistant_path.rstrip().lstrip()
        try:
            properly_loaded = self.env.load_assistant(self.assistant_path)
        except Exception as exc_:
            self.logger.error(f"Error in load_assistant: {exc_}")
            return [f"❌ {exc_}", dash.no_update]
        clear = 0
        if properly_loaded:
            res = self.format_path(os.path.abspath(self.assistant_path))
            res = f"🤖 {res}"
            clear = 1
        else:
            res = ""
        return [res, clear]

    def clear_loading(self, need_clearing):
        """once an assistant has been """
        if need_clearing == 0:
            raise dash.exceptions.PreventUpdate
        return [""]

    def save_expe(self, button, save_expe_path):
        """
        This callback save the experiment using a grid2op runner.

        work in progress !

        TODO: reuse the computation of the environment instead of creating a runner for such purpose !
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            raise dash.exceptions.PreventUpdate

        if self.env.is_computing():
            # cannot save while an experiment is running
            msg_ = "environment is still computing"
            self.logger.info(f"save_expe: {msg_}")
            return [f"⌛ {msg_}"]

        if save_expe_path is None:
            msg_ = "invalid path (None)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}"]

        self.save_expe_path = save_expe_path.rstrip().lstrip()
        if not os.path.exists(self.save_expe_path):
            msg_ = "invalid path (does not exists)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}"]
        if not os.path.isdir(self.save_expe_path):
            msg_ = "invalid path (not a directory)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}"]
        self.logger.info(f"saving experiment in {self.save_expe_path}")
        self.env.start_computation()  # prevent other type of computation
        try:
            env = self.env.glop_env.copy()
            nb_step = self.env.obs.current_step
            chro_id = env.chronics_handler.get_id()
            from grid2op.Runner import Runner
            from grid2op.Agent import FromActionsListAgent
            list_action = self.env.get_current_action_list()
            agent = FromActionsListAgent(env.action_space, list_action)
            dict_ = env.get_params_for_runner()
            if "logger" in dict_:
                # don't use the logger of the grid2op environment
                del dict_["logger"]
            runner = Runner(**dict_,
                            agentClass=None,
                            agentInstance=agent,
                            logger=self.logger,
                            )
            runner.run(nb_episode=1,
                       path_save=self.save_expe_path,
                       episode_id=[chro_id],
                       max_iter=max(nb_step + 1, 2),
                       env_seeds=[self.env.glop_env.seed_used],  # TODO. in case of "reset" this might not work
                       # agent_seeds=[self.], TODO... This might require deep rework of this function !
                       pbar=True)
            res = f"✅ saved in \"{self.save_expe_path}\""
        except Exception as exc_:
            self.logger.error(f"save_expe exception while trying to save the experiment: {exc_}")
            res = f"❌ Something went wrong during the saving of the experiment. Error: {exc_}"
        finally:
            # ensure I stop the computation that i fake to start here
            self.env.stop_computation()  # prevent other type of computation
        return [res]

    def timeline_set_time(self, time_line_graph_clicked):
        if self.env.is_computing():
            # nothing is updated if i am doing a computation
            raise dash.exceptions.PreventUpdate

        if time_line_graph_clicked is None:
            # I did no click on anything
            raise dash.exceptions.PreventUpdate

        res = self.env.handle_click_timeline(time_line_graph_clicked)
        self.is_previous_click_end = True  # hack to have the progress bar properly recomputed
        return [res]
