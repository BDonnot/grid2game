.. Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
   See AUTHORS.txt
   This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
   If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
   you can obtain one at http://mozilla.org/MPL/2.0/.
   SPDX-License-Identifier: MPL-2.0
   This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

Welcome to Grid2Game documentation!
=========================================
Grid2Game is a python package that allows you to interact with a powergrid (using grid2op action types).

It allows to:

- "play" the game as if you were operating a powergrid
- inspect the state of powergrid visually
- inspect the past state of the grid (with the productions, loads as well as maximum flows on the powerlines)
- design some basic collaboration between an agent (called "assistant" in this package) and a human, by having
  the assistant proposing actions to the human
- save the current experiment in a standardized manner (using the grid2op runner) that can be read
  back with grid2op (for example if you want to perform some kind of supervized learning or an agent)
  or with grid2viz (for manual a posteriori examination)

.. toctree::
   :maxdepth: 2
   :caption: Quickstart

   quickstart
   play_the_game
   help_your_agent
   imitation_learning


Technical Documentation (work in progress)
-------------------------------------------

This is a work in progress at the moment

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   load_assistant
   save_expe
   control_scenario
   navigate_in_scenario
   control_display
   timeline
   grid_displayed
   available_action
   temporal_data


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
