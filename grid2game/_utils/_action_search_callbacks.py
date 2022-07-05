# Copyright (c) 2019-2022, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import dash 

from .utils_import import html, dcc, dbc


def add_callbacks(dash_app, viz_server):    
    dash_app.callback([dash.dependencies.Output("trigger_computation_as", "n_clicks"),
                       dash.dependencies.Output("scenario_progression_as", "value"),
                       dash.dependencies.Output("scenario_progression_as", "label"),
                       dash.dependencies.Output("scenario_progression_as", "color"),
                       dash.dependencies.Output("timeline_graph_as", "figure"),
                       dash.dependencies.Output("rt_date_time_as", "children"),
                       dash.dependencies.Output("real-time-graph_as", "figure"),
                       dash.dependencies.Output("hidden_output_explore", "n_clicks"),
                       dash.dependencies.Output("is_computing_left_as", "style"),
                       dash.dependencies.Output("is_computing_right_as", "style"),],
                      [dash.dependencies.Input('refresh-button_as', "n_clicks"),
                       dash.dependencies.Input('explore-button_as', "n_clicks"),
                       dash.dependencies.Input("timer_as", "n_intervals")]
                      )(viz_server.main_action_search)
    
    dash_app.callback([dash.dependencies.Output("main_action_search_trigger_rt", "n_clicks"),
                       dash.dependencies.Output("main_action_search_trigger_for", "n_clicks")
                      ],
                      [dash.dependencies.Input("trigger_computation_as", "n_clicks"),
                       dash.dependencies.Input("recompute_rt_from_timeline_as", "n_clicks")
                      ]
                      )(viz_server.computation_wrapper)
    
    # callback for the timeline
    dash_app.callback([dash.dependencies.Output("recompute_rt_from_timeline_as", "n_clicks")],
                      [dash.dependencies.Input('timeline_graph_as', 'clickData')]
                      )(viz_server.timeline_set_time)
