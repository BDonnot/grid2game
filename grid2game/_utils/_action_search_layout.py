# Copyright (c) 2019-2022, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

from .utils_import import html, dcc, dbc


def setupLayout(viz_server):
    rt_graph_label = html.H3(viz_server._rt_graph_label ,
                             style={"alignItems": "center",
                                   "justifyContent": "center"})
    rt_date_time = html.Div([html.H6(viz_server.rt_datetime, 
                                     id="rt_date_time_as"),],
                            style={"display": "flex",
                                   "alignItems": "center",
                                   "justifyContent": "center"})
    real_time_graph = dcc.Graph(id="real-time-graph_as",
                                config={
                                    'displayModeBar': False,
                                    "responsive": True,
                                    "autosizable": True
                                },
                                figure=viz_server.real_time)
    
    rt_graph_div = html.Div(id="rt_graph_div_as",
                        children=[
                            rt_graph_label,
                            rt_date_time,
                            html.H6("⚠️ Previous action illegal ⚠️",
                                    style=viz_server._style_legal_info,
                                    id="rt_extra_info_as"),
                            real_time_graph,
                        ],
                        style={'display': 'inline-block',
                               "alignItems": "center",
                               "justifyContent": "center",
                               'width': '50%',
                               "height": viz_server._graph_height
                              }
                        )
    
    # progress in the scenario (progress bar and timeline)
    progress_bar_for_scenario = html.Div(children=[html.Div(dbc.Progress(id="scenario_progression_as",
                                                                         value=0.,
                                                                         max=100.,
                                                                         label="0%",
                                                                         color="danger"),
                                                            ),
                                                    html.Div(dcc.Graph(id="timeline_graph_as",
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
    graph_tmp = html.Div([
                progress_bar_for_scenario,
                rt_graph_div,
            ])
    return graph_tmp
