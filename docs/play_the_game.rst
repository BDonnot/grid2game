.. Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
   See AUTHORS.txt
   This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
   If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
   you can obtain one at http://mozilla.org/MPL/2.0/.
   SPDX-License-Identifier: MPL-2.0
   This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

.. |control_panel_chronic| image:: ./img/ControlPanel_chronic.png
.. |control_panel_seed| image:: ./img/ControlPanel_seed.png
.. |control_panel_reset| image:: ./img/ControlPanel_reset.png
.. |grid_timeline_scen_info| image:: ./img/grid_timeline_scen_info.png
.. |control_panel_control_buttons| image:: ./img/ControlPanel_scenario_control.png

.. _page_play_the_game:

First usage example: play the "grid2op game"
=============================================

Once you started a grid2game server with a given grid2op environment, you can easily
start operating the grid on a given scenario (a scenario is analogous to a "level" in a video
game).

Choose a scenario
---------------------
To choose a scenarion, you simply need to click on the dropdown list:

|control_panel_chronic|

As some environments are stochastic, you might also want to chose a seed for this scenario (
if you use the same seed on the same scenario, all the "stochastic" components will be
the same. For example, maintenance operations will happen exactly at the same time, concern 
the same powerline, the opponent will attack at the same time for the
same duration etc.)

This can also be achieved in the GUI by entering a number in the appropriate field:

|control_panel_seed|

Once done, you will need to "reset" the environment by pressing the "reset" button:

|control_panel_reset|

And you can start operating the grid !

To make sure the scenario is properly configured, you can have a look at the information just above the
grah of the powergrid:

|grid_timeline_scen_info|

(in this example, the scenario named "0002" has been selected and no seed has been set)

Play interactively
---------------------

Once the scenario is loaded, you can interact with the grid just like any "agent". Here are the 
main commands similar to "env.step(action)"

.. note::

    We will explain in the next section (:ref:`sec_play_the_game_action`) how to chose the action

All the interesting buttons are located there:

|control_panel_control_buttons|

In this "quickstart" we only detail a few of them. More information can be found in the dedicated
page: :ref:`page_step_back_end` .

TODO

Step
~~~~~~~~

+12
~~~~~~~~~

End
~~~~

.. _sec_play_the_game_action:

Choose an action
-----------------

TODO