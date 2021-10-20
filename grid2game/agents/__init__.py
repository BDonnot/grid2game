# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import sys
import os
from grid2op.Agent import BaseAgent


def load_assistant(assistant_path, assistant_seed, env, logger=None):
    """utility to load the agent"""
    # lazy loading
    res = None
    if logger is not None:
        my_logger = logger.getChild("load_assistant_function")
        my_logger.info(f"Loading an assistant with \"load_assistant\": {assistant_path = }")
    if assistant_path is not None:
        abs_assistant_path = os.path.abspath(assistant_path)
        if not os.path.exists(assistant_path):
            msg_ = f"Nothing found at \"{assistant_path}\""
            if logger is not None:
                my_logger.error(msg_)
            raise RuntimeError(msg_)
        if not os.path.isdir(assistant_path):
            msg_ = f"\"{assistant_path}\" should be a folder"
            if logger is not None:
                my_logger.error(msg_)
            raise RuntimeError(msg_)

        if not os.path.exists(os.path.join(assistant_path, "submission")):
            msg_ = f"\"{assistant_path}\" should contain a folder named \"submission\""
            if logger is not None:
                my_logger.error(msg_)
            raise RuntimeError(msg_)

        sys.path.append(abs_assistant_path)
        try:
            from submission import make_agent
            res = make_agent(env.copy(), os.path.join(abs_assistant_path, "submission"))
            if not isinstance(res, BaseAgent):
                msg_ = "your assistant you be a grid2op.Agent.BaseAgent"
                if logger is not None:
                    my_logger.error(msg_)
                raise RuntimeError(msg_)
        except Exception as exc_:
            if logger is not None:
                my_logger.error(f"Impossible to load your agent. Make sure to include properly the \"make_agent\" "
                                f"function. Error was {exc_}")
            raise
        if logger is not None:
            my_logger.info("assistant loaded in \"load_assistant\"")
        res.seed(int(assistant_seed))
    return res
