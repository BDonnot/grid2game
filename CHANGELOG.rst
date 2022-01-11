Change Log
===========

[TODO]
--------------------

- [???] add possibility to toggle on / off the control button with line unit, line side, etc.
- [???] hide the "forecast" view in go / gofast and even in step if nothing is being simulated
- [???] hide the "action" panel in go / go fast mode to show directly the temporal series.
- [???] make a "mode" where you **cannot** go "backward"

[0.2.0] - 2022-xx-yy
----------------------
- [IMPROVED] progress bar updates during computation (even if nothing else does)
- [IMPROVED] illegal actions are now displayed on the GUI (see https://github.com/BDonnot/grid2game/issues/3) 
- [IMPROVED] when creating a topological action, the graph of the substation is updated "on the fly" (see https://github.com/BDonnot/grid2game/issues/36) 
- [IMPROVED] buses having 2 or more activated buses are displayed in a different color (see https://github.com/BDonnot/grid2game/issues/35) 

[0.1.0] - 2022-01-10
----------------------
- [ADDED] fix the Action panel, by adding a "manual" pre selection and a "manual" mode, instead of having to always click
  and unclick to "do nothing"
- [ADDED]  a saving method, that save the experiments played currently (using the runner and an agent reading an
  action list, might require to upgrade the runner api to play only certain scenarios)
- [ADDED] add alarm feature : stop the computation if the assistant raises an alarm
- [ADDED] have everything go through the "env.do_computation()" interface and not "hack" it, like for the assistant
  for example (where `self.env.next_action_is_dn()`, `self.env.next_action_is_assistant()` or
  `self.env.next_action_is_previous()` are directly called by the VizServer)
- [ADDED] add the name of the current scenario next to the "reset"
- [ADDED] make a button so select a scenario next to the "reset" button too
- [ADDED] the timeline: a "chronological stuff" where you could "branch" and "navigate". For example, you could get
  advance to a given step, make an action, and then with a simple click to at the time you did the action
  to test another one.
- [ADDED] basic documentation at https://grid2game.readthedocs.io/en/latest/
- [ADDED] hosted app on heroku (https://grid2game.herokuapp.com/) where people can explore the possibility
  of the app on the "educ_case14_storage" environment.

[0.0.2]
---------
- [ADDED] capability to change the parameters of the grid2op environments (command `--g2op_param XXX`).
- [ADDED] capability to change the building of the environment (command `--g2op_config XXX`).
- [ADDED] possibility to change the number of steps performed "at once"
