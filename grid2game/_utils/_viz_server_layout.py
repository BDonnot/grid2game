# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

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


def setupLayout(viz_server):
    # layout of the app
    # TODO split that in multiple subfunctions

    # Header
    title = html.H1(children='Grid2Game')
    header = html.Header(id="header", className="row w-100", children=[title])

    # App
    button_css = "" # col-6 col-sm-6 col-md-3 col-lg-3 col-xl-1"
    reset_button = html.Label("Reset",
                              id="reset-button",
                              n_clicks=0,
                              className="btn btn-primary")
    # reset_button_dummy = html.P("", style={'display': 'none'})
    reset_col = html.Div(id="reset-col",
                         children=[reset_button,
                                   html.Div([# html.P("Chronics: ", style={"marginRight": 5, "marginLeft": 5}),
                                             html.Div([dcc.Dropdown(id="chronic_names",
                                                                    placeholder="Select a chronic",
                                                                    options=[{"value": el, "label": el} 
                                                                             for el in viz_server.env.list_chronics()])
                                                      ],
                                                      id="chronics_dropdown",
                                                      style={"width": "100%"}),
                                           ],
                                           id="chronics_selector",
                                           style={"display": "flex", "minWidth": "20%", "marginRight": "10", "marginLeft": "10"}),
                                    html.Div([
                                              dcc.Input(id="set_seed",
                                                        type="number",
                                                        placeholder="Select a seed",
                                                       ),        
                                             ],
                                             id="seed_selector")
                                  ],
                         style={"display": "flex",
                                # 'justify-content': 'space-between'
                                }
                         )

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
    nb_step_go_fast = dcc.Input(
        id="nb_step_go_fast",
        type="number",
        placeholder="steps",
    )                     
    go_fast = html.Label(children =f"+ {viz_server.nb_step_gofast}",
                         id="gofast-button",
                         n_clicks=0,
                         className="btn btn-primary",
                        )
    go_till_game_over = html.Label("End",
                                   id="go_till_game_over-button",
                                   n_clicks=0,
                                   className="btn btn-primary",
                                  )
    # html display
    # see https://dash.plotly.com/dash-core-components/loading
    # [dcc.Loading(id="loading_go_fast_", type="circle", children=html.Div(id="loading_go_fast_output"))]
    is_computing_left = html.Div(children=[html.P("⏳ Computing ⏳", style={'color': 'red', "fontSize": "x-large"})],
                                 id="is_computing_left",
                                 style={'display': 'none'})
    is_computing_right = html.Div(children=[html.P("⏳ Computing ⏳", style={'color': 'red', "fontSize": "x-large"})],
                                  id="is_computing_right",
                                  style={'display': 'none'})

    controls_row = html.Div(id="control-buttons",
                            # className="row",
                            children=[
                                is_computing_left,
                                back_button,  # TODO display back only if its possible in the viz_server.env
                                step_button,
                                simulate_button,
                                go_butt,
                                html.Div([nb_step_go_fast,
                                          go_fast],
                                          id="control_nb_step_fast",
                                          style= {"display": "flex"}),
                                go_till_game_over,
                                is_computing_right
                            ],
                            style={'justifyContent': 'space-between',
                                   "display": "flex"}
                            )

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
                             ],
                             value='none',
                             clearable=False)

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
    # load_info_div = html.Div(id="load-info", children=[load_info_label, load_info])

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
    button_css_class = "unit_buttons"
    style_button = {"minWidth": "15%"}
    lineinfo_col = html.Div(id="lineinfo-col",
                            className=button_css_class,
                            children=[line_info_label, line_info],
                            style=style_button
                            )
    lineside_col = html.Div(id="lineside-col", className=button_css_class, children=[line_side_label, line_side], style=style_button)
    loadinfo_col = html.Div(id="loadinfo-col", className=button_css_class, children=[load_info_label, load_info], style=style_button)
    geninfo_col = html.Div(id="geninfo-col", className=button_css_class, children=[gen_info_label, gen_info], style=style_button)
    storinfo_col = html.Div(id="storinfo-col", className=button_css_class, children=[stor_info_label, stor_info], style=style_button)

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
                            style={"display": "flex",
                                   'justifyContent': 'space-between'},
                            )
    if viz_server._app_heroku:
        assistant_txt = "Feature currently unavailable on heroku"
        save_txt = "Feature currently unavailable on heroku"
        btn_assistant_save = "btn btn-secondary"
    else:
        assistant_txt = 'Copy paste assistant location'
        save_txt = 'Where do you want to save the current experiment?'
        btn_assistant_save = "btn btn-primary"

    select_assistant = html.Div(id='select_assistant_box',
                                children=[html.Div(children=[dcc.Input(placeholder=assistant_txt,
                                                                       id="select_assistant",
                                                                       type="text",
                                                                       style={
                                                                        'width': '70%',
                                                                        'lineHeight': '55px',
                                                                        'verticalAlign': 'middle',
                                                                             }
                                                                       ),
                                                             html.P(viz_server.format_path(viz_server.assistant_path),
                                                                    id="current_assistant_path",
                                                                    style={'width': '28%',
                                                                           'textAlign': 'center',
                                                                           'verticalAlign': 'middle',
                                                                           "margin": "0",
                                                                           }
                                                                   ),
                                                            ],
                                                   style={'borderWidth': '1px',
                                                          'borderStyle': 'dashed',
                                                          'borderRadius': '5px',
                                                          'width': '100%',
                                                          "display": "flex",
                                                          "alignItems":"center",
                                                          "paddingTop": "5px",
                                                          "paddingBottom": "5px",
                                                          "paddingLeft": "2px",
                                                          "paddingRight": "2px"
                                                         }
                                                  ),
                                          html.Label("load",
                                                     id="load_assistant_button",
                                                     n_clicks=0,
                                                     className=btn_assistant_save,
                                                     style={ 'width': '100%', }
                                                    ),
                                         ]
                               )

    save_experiment = html.Div(id='save_expe_box',
                               children=[                  
                               html.Div(children=[
                                   dcc.Input(placeholder=save_txt,
                                             id="save_expe",
                                             type="text",
                                             style={
                                                 'width': '70%',
                                                 'height': '55px',
                                                 'lineHeight': '55px',
                                                 'verticalAlign': 'middle',
                                                #  "margin-top": 5,
                                                #  "margin-left": 20
                                                 }),
                                    html.P(viz_server.format_path(viz_server.assistant_path),
                                           id="current_save_path",
                                           style={'width': '28%',
                                                  'textAlign': 'center',
                                                  'height': '55px',
                                                  'verticalAlign': 'middle',
                                                  "margin": "0",
                                                #   "margin-top": 20
                                                  }
                                           ),
                                                 ],
                                        style={
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        "display": "flex",
                                        "alignItems":"center",
                                        # "padding": "2px",
                                        "paddingTop": "5px",
                                        "paddingBottom": "5px",
                                        "paddingLeft": "2px",
                                        "paddingRight": "2px"
                                        # 'margin': '10px'
                                              }
                                       ),
                               html.Label("save",
                                          id="save_expe_button",
                                          n_clicks=0,
                                          className=btn_assistant_save,
                                          style={'height': '35px',
                                                 'width': '100%',
                                                }
                                         ),
                                        ]
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
                                                                         max=100.,
                                                                         color="danger"),
                                                            ),
                                                    html.Div(dcc.Graph(id="timeline_graph",
                                                                        config={
                                                                            "responsive": True,
                                                                            },
                                                                        figure=viz_server.fig_timeline,
                                                                        style={"height": '10vh'}
                                                                        ),

                                                            ),
                                                    html.Br(),
                                                    ],
                                            )

    ### Graph widget
    real_time_graph = dcc.Graph(id="real-time-graph",
                                config={
                                    'displayModeBar': False,
                                    "responsive": True,
                                    "autosizable": True
                                },
                                figure=viz_server.real_time)
    simulate_graph = dcc.Graph(id="simulated-graph",
                               config={
                                    'displayModeBar': False,
                                    "responsive": True,
                                    "autosizable": True
                                },
                               figure=viz_server.forecast)

    graph_css = "col-12 col-sm-12 col-md-12 col-lg-12 col-xl-7 "\
                "order-last order-sm-last order-md-last order-xl-frist " \
                "d-md-flex flex-md-grow-1 d-xl-flex flex-xl-grow-1"
    graph_css = "six columns"
    rt_graph_label = html.H3("Real time observation:", style={'textAlign': 'center'})
    rt_date_time = html.P(viz_server.rt_datetime, style={'textAlign': 'center'}, id="rt_date_time")
    rt_graph_div = html.Div(id="rt_graph_div",
                            children=[
                                rt_graph_label,
                                rt_date_time,
                                real_time_graph],
                            style={'display': 'inline-block',
                                   'width': '50%',
                                  }
                            )
    forecast_graph_label = html.H3("Forecast (t+5mins):", style={'textAlign': 'center'})
    forecast_date_time = html.P(viz_server.for_datetime, style={'textAlign': 'center'}, id="forecast_date_time")
    sim_graph_div = html.Div(id="sim_graph_div",
                                children=[
                                    forecast_graph_label,
                                    forecast_date_time,
                                    simulate_graph],
                                style={'display': 'inline-block',
                                       'width': '50%',
                                       }
                                )
    scenario_label = html.H3(f"Scenario: {viz_server.env.scenario_id()}",
                             style={'textAlign': 'center'},
                             id="scenario_id_title")
    seed_label = html.H4(f"(seed: {viz_server.seed})",
                         style={'textAlign': 'center'},
                         id="scenario_seed_title")
    graph_col = html.Div(id="graph-col",
                         children=[scenario_label, seed_label, rt_graph_div, sim_graph_div],
                         style={'height': '75vh'},
                         )

    # page to click the data
    # see https://dash.plotly.com/interactive-graphing

    # ### Action widget
    current_action = html.Pre(id="current_action")
    which_action_button = dcc.Dropdown(id='which_action_button',
                                       options=[
                                           {'label': 'do nothing', 'value': 'dn'},
                                           {'label': 'previous', 'value': 'prev'},
                                           {'label': 'assistant', 'value': 'assistant'},
                                           {'label': 'manual', 'value': 'manual'},
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
    generator_clicked = html.Div(children=[html.P("Generator id", id="gen-id-clicked"),
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
                                    style={'display': 'inline-block'}
                                )
    storage_clicked = html.Div(children=[html.P("Storage id", id="stor-id-clicked"),
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
                                style={'display': 'inline-block'}
                              )
    line_clicked = html.Div(children=[html.P("Line id", id="line-id-clicked"),
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
                            style={'display': 'inline-block'}
                            )
    sub_clicked = html.Div(children=[html.P("sub id", id="sub-id-clicked"),
                                     html.P("New Topology:"),
                                     dcc.Graph(id="graph_clicked_sub",
                                               config={},
                                               style={}
                                              ),
                                     html.P("",
                                            id="sub-id-hidden",
                                            style={'display': 'none'}
                                           )
                                    ],
                            id="sub_clicked",
                            style={'display': 'inline-block',
                                   'width': '100%',
                                  }
                            )

    # Title
    action_widget_title = html.Div(id="action_widget_title",
                                   children=[html.P("Action:  "),
                                             which_action_button],
                                   style={},
                                  )
    # display the action
    layout_click = html.Div(id="action_clicked",
                            children=[generator_clicked,
                                      storage_clicked,
                                      line_clicked,
                                      sub_clicked],
                            style={"width": "59%",})
    # action as text
    action_col = html.Div(id="action_widget",
                          children=[current_action],
                          style={'width': '39%'}
                          )
    
    # combine both
    interaction_and_action = html.Div([action_widget_title,
                                       html.Div([layout_click,
                                                 action_col],
                                                 id="action_display",
                                                 style={"width": "100%", "display": "flex"})
                                      ],
                                      id="action_select_and_print",
                                      style={"width": "100%"},
                                     )

    ## temporal graphs
    graph_gen_load = dcc.Graph(id="graph_gen_load",
                               config={
                                    'displayModeBar': False,
                                    "responsive": True,
                                    "autosizable": True
                               },
                               style={'display': 'block'},
                               figure=viz_server.fig_load_gen)
    graph_flow_cap = dcc.Graph(id="graph_flow_cap",
                               config={
                                    'displayModeBar': False,
                                    "responsive": True,
                                    "autosizable": True
                                      },
                               style={'display': 'block'},
                               figure=viz_server.fig_line_cap)

    temporal_graphs = html.Div([html.Div([graph_gen_load],
                                            className=graph_css,
                                            style={'display': 'inline-block',
                                                   'width': '50%', # 'height': '47vh'
                                                }),
                                html.Div([graph_flow_cap],
                                            className=graph_css,
                                            style={'display': 'inline-block',
                                                   'width': '50%', # 'height': '47vh'
                                                })
                                ],
                                style={'width': '100%'},
                                # className="row",
                                id="temporal_graphs")

    # hidden control button, hack for having same output for multiple callbacks
    interval_object = dcc.Interval(id='interval-component',
                                   interval=viz_server.time_refresh * 1000,  # in milliseconds
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
    change_graph_title = html.Label("", id="change_graph_title", n_clicks=0)
    chronic_names_dummy_output = html.Label("", id="chronic_names_dummy_output", n_clicks=0)
    set_seed_dummy_output = html.Label("", id="set_seed_dummy_output", n_clicks=0)
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
                                    trigger_computation, recompute_rt_from_timeline, change_graph_title,
                                    chronic_names_dummy_output, set_seed_dummy_output
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
                            # state_row,  # the two graphs of the grid
                            graph_col,  # the two graphs of the grid
                            html.Br(),
                            interaction_and_action,
                            html.Br(),
                            temporal_graphs,
                            interval_object,
                            hidden_interactions,
                            timer_callbacks
                        ])

    return layout
