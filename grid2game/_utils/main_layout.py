
# Copyright (c) 2019-2022, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

from dash import Dash

from .utils_import import html, dcc


def setupLayout(viz_server, *tabs):
    layout = html.Div([
        html.H1('Grid2game'),
        dcc.Tabs(id="tabs-example-graph",
                 value='tab-1-example-graph',
                 children=tabs),
        html.Div(id='tabs-content-example-graph')
    ])
    return layout
