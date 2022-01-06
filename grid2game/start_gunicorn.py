# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import flask
from grid2game.VizServer import VizServer
server = flask.Flask(__name__)  # define flask app.server

dev = False
is_test = False
env_name = "l2rpn_case14_sandbox"
env_seed = None
assistant_seed = None
assistant_path = ""


class Args:
    pass

args = Args()
args.env_name = env_name
args.dev = dev
args.is_test = is_test
args.env_seed = env_seed
args.assistant_path = assistant_path
args.assistant_seed = assistant_seed
args.g2op_param = None
args.g2op_config = None


viz_server = VizServer(server=server, build_args=args)
app = viz_server.my_app

if __name__ == '__main__':
    app.run_server(debug=args.dev)
