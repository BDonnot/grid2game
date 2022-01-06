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


Technical Documentation (work in progress)
-------------------------------------------

This is a work in progress at the moment

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   load_assistant
   control_scenario
   navigate_in_scenario
   available_action
   timeline
   temporal_data
   save_expe


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
