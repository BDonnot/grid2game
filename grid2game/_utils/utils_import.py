# Copyright (c) 2019-2022, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

"""Handles different imports based on dash version."""


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

