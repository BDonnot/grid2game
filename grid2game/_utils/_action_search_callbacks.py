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
    dash_app.callback([dash.dependencies.Output("scenario_progression_as", "value"),
                       dash.dependencies.Output("scenario_progression_as", "label"),
                       dash.dependencies.Output("scenario_progression_as", "color"),
                       dash.dependencies.Output("timeline_graph_as", "figure"),
                       dash.dependencies.Output("rt_date_time_as", "children"),
                       dash.dependencies.Output("real-time-graph_as", "figure"),
                      ],
                      [dash.dependencies.Input('refresh-button_as', "n_clicks")]
                     )(viz_server.refresh_state_for_as_graph)   
    
    dash_app.callback([dash.dependencies.Output("hidden_output_explore", "n_clicks")],
                      [dash.dependencies.Input('explore-button_as', "n_clicks")]
                      )(viz_server.search_topk_actions)
