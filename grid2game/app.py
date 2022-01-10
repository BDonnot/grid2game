#!/usr/bin/env python3

# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.


import argparse

from grid2game.VizServer import VizServer


def cli():
    parser = argparse.ArgumentParser(description="Grid2Op-Viz")
    parser.add_argument("--dev", required=False,
                        action="store_true", default=False,
                        help="Enable debug mode")
    parser.add_argument("--is_test", required=False,
                        action="store_true", default=False,
                        help="Create and environment with keyword argument \"test=True\"")
    parser.add_argument("--env_name", required=False,
                        default="rte_case14_realistic", type=str,
                        help="Name of the environment to create")
    parser.add_argument("--env_seed", required=False,
                        default=0, type=int,
                        help="Seed of the environment")

    # TODO
    parser.add_argument("--assistant_seed", required=False,
                        default=0, type=int,
                        help="Seed of the assistant")

    parser.add_argument("--assistant_path", required=False,
                        default="", type=str,
                        help="path where the \"make_agent\" function is defined")

    # TODO better parameters
    parser.add_argument("--g2op_param", required=False,
                    default="", type=str,
                    help="path to look for grid2op environment parameters (used in env.change_parameters(g2op_param)).")
    parser.add_argument("--g2op_config", required=False,
                    default="", type=str,
                    help="path to look for grid2op config parameters (used in env.make(..., **g2op_config)).")

    # TODO for backend too

    # TODO add an option to change the parameters of the environment

    parser.add_argument("--_app_heroku", required=False,
                        action="store_true", default=False,
                        help="INTERNAL: do not use (inform that the app is running on the heroku server)")

    return parser.parse_args()


def get_viz_server(server=None):
    args = cli()
    viz_server = VizServer(build_args=args, server=server)
    return args.dev, viz_server


def start_cli():
    debug, viz_server = get_viz_server()
    viz_server.run_server(debug=debug)


if __name__ == '__main__':
    start_cli()
