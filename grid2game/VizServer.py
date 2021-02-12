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

        # reset has been called
        self.app.callback([dash.dependencies.Output("dummy-for-reset-hidden", "children")],
                          [dash.dependencies.Input('reset-button', 'n_clicks')])(self.has_reset)

        # callback for the "continue" button
        self.app.callback([dash.dependencies.Output("step-button", "className"),
                           dash.dependencies.Output("simulate-button", "className"),
                           dash.dependencies.Output("back-button", "className"),
                           dash.dependencies.Output("reset-button", "className"),
                           dash.dependencies.Output("continue_til_go-button", "className"),
                           dash.dependencies.Output("step-button", "n_clicks"),  # callback to call the "plot function"
                           # dash.dependencies.Output("continue_til_go-button", "n_clicks")
                           ],
                          [dash.dependencies.Input('interval-component', 'n_intervals'),
                           dash.dependencies.Input("continue_til_go-button", "n_clicks"),
                           dash.dependencies.Input("go_fast-button", "n_clicks"),],
                          [
                           dash.dependencies.State("step-button", "n_clicks")
                          ]
                          )(self.advance_time)

        # Register controls update callback (unit information, step and simulate)
        self.app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                           dash.dependencies.Output("simulated-graph", "figure"),
                           dash.dependencies.Output("rt_date_time", "children"),
                           dash.dependencies.Output("forecast_date_time", "children"),
                           dash.dependencies.Output("graph_gen_load", "figure"),
                           dash.dependencies.Output("graph_flow_cap", "figure"),
                           ],
                           [dash.dependencies.Input("step-button", "n_clicks"),
                            dash.dependencies.Input("simulate-button", "n_clicks"),
                            dash.dependencies.Input("back-button", "n_clicks"),
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
                           ],
                          [dash.dependencies.Input("real-time-graph", "clickData"),
                           # dash.dependencies.Input("step", "n_clicks"),
                           # dash.dependencies.Input("simulate", "n_clicks"),
                           ])(self.display_click_data)

        # print the current action
        self.app.callback([dash.dependencies.Output("current_action", "children"),
                           ],
                          [
                            # dash.dependencies.Input("step", "n_clicks"),
                            # dash.dependencies.Input("simulate", "n_clicks"),
                            dash.dependencies.Input("gen-id-hidden", "children"),
                            dash.dependencies.Input('gen-dispatch', "value"),
                            dash.dependencies.Input("storage-id-hidden", "children"),
                            dash.dependencies.Input('storage-power-input', "value"),
                            dash.dependencies.Input("line-id-hidden", "children"),
                            dash.dependencies.Input('line-status-input', "value"),
                          ])(self.display_action)

        # collapse the temporal information
        self.app.callback([dash.dependencies.Output('temporal-graphs', "style")],
                          [dash.dependencies.Input('show-temoral-graph', "value")])(self.show_tmeporal_graphs)

    def setupLayout(self):
        # layout of the app

        # Header
        title = html.H1(children='Grid2Game')
        header = html.Header(id="header", className="row w-100", children=[title])

        # App
        reset_button = html.Label("Reset",
                                  id="reset-button",
                                  n_clicks=0,
                                  className="btn btn-primary")
        reset_button_dummy = html.P("", id="dummy-for-reset-hidden", style={'display': 'none'})

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
                                            options=[{'label': 'Display time series', 'value': 'display'}],
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
                                    })
        graph_flow_cap = dcc.Graph(id="graph_flow_cap",
                                   config={
                                       'displayModeBar': False,
                                       "responsive": True,
                                       "autosizable": True
                                   })

        temporal_graphs = html.Div([html.Div([graph_gen_load],
                                             className=graph_css,
                                             style={'display': 'inline-block',
                                                    'width': '50vh', 'height': '47vh'}),
                                    html.Div([graph_flow_cap],
                                             className=graph_css,
                                             style={'display': 'inline-block',
                                                    'width': '50vh', 'height': '47vh'})
                                    ],
                                   style={'display': 'block'},
                                   className="row",
                                   id="temporal-graphs")
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
                              interval_object
                          ])
        return layout

    def show_tmeporal_graphs(self, show_temporal_graph):
        """handles the action that displays (or not) the time series graphs"""
        if show_temporal_graph:
            return [{'display': 'block'}]
        return [{'display': 'none'}]

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

    def make_step(self):
        self.env.step()
        self.update_obs_fig()

    def update_obs_fig(self):
        self.plot_grids.update_rt(self.env.obs)
        self.plot_grids.update_forecat(self.env.sim_obs)
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.plot_temporal.update_trace()

    def has_reset(self, reset_clicks):
        if self.is_continue_mode:
            # do not reset if in "continue to simulate" mode
            return ["toto"]

        if self.reset_clicks < reset_clicks:
            self.reset_clicks = reset_clicks
            self.env.reset()
            self.update_obs_fig()
        return ["toto"]

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

        if self.back_clicks < back_clicks:
            # "back" has been clicked
            self.back_clicks = back_clicks
            if self.is_continue_mode is False:
                self.env.back()
                self.update_obs_fig()

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
