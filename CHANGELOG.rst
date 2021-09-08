Change Log
===========

[TODO]
--------------------
- [???] fix the Action panel, by adding a "manual" pre selection and a "manual" mode, instead of having to always click
  and unclick to "do nothing"
- [???] add a saving method, that save the experiments played currently (using the runner and an agent reading an
  action list, might require to upgrade the runner api to play only certain scenarios)
- [???] improve layout, especially hard coded figure width and co
- [???] add possibility to toggle on / off the control button with line unit, line side, etc.
- [???] hide the "forecast" view in go / gofast and even in step if nothing is being simulated
- [???] add alarm feature : stop the computation if the assistant raises an alarm
- [???] have everything go through the "env.do_computation()" interface and not "hack" it, like for the assistant
  for example (where `self.env.next_action_is_dn()`, `self.env.next_action_is_assistant()` or
  `self.env.next_action_is_previous()` are directly called by the VizServer)
- [???] add the name of the current scenario next to the "reset"
- [???] make a button so select a scenario next to the "reset" button too
- [???] make a "mode" where you cannot go "backward"
- [???] have a "chronological stuff" where you could "branch" and "navigate". For example, you could get
  advance to a given step, make an action, and then with a simple click to at the time you did the action
  to test another one.