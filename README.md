# grid2game

This package proposes a GUI (Graphical User Interface) to interact with any grid2op environment.

It allows human and possibly an "assistant" (aka an "agent", for example developed in the context of the `L2RPN <https://l2rpn.chalearn.org/>`_ competitions) to interact together in the powergrid operations.


## Disclaimer
This package is still in "early alpha" mode.

Performances are not that great and some useful features are still missing. The layout is also relatively "ugly" 
at the moment.


## Installation
To install the package, you need to install it from source:
```commandline
python3 -m pip install git+https://github.com/BDonnot/grid2game.git
``` 

An alternative is to clone the repository, and then install it from there:
```commandline
git clone https://github.com/BDonnot/grid2game.git
cd grid2game
python3 install -e .
```

**IMPORTANT** In all cases, we highly recommend to perform these modifications inside a python virtual environment (for example using `conda create -n grid2game_env; conda activate grid2game_env` or `python -m virtualenv grid2game_env; source/grid2game_env/bin/activate`).

**NOTE** It will install some dependencies and will require, in particular grid2op >= 1.6.4. The use of `lightsim2grid <https://github.com/BDonnot/lightsim2grid>`_ is also highly recommended.

## Usage

Once installed, you should be able to use the `grid2game` command from your shell / bash / windows powershell.

You can use it this way:

```commandline
grid2game --dev --env_name educ_case14_storage --is_test
```

- `--dev` specifies that the dash server will run in "dev" mode, we recommend you to use it
- `--env_name educ_case14_storage` specifies that the application will run the `educ_case14_storage`
  environment
- `--is_test` specifies that the grid2op environment will be built with `test=True` (so in this 
  case `grid2op.make("educ_case14_storage", test=True))

You can also add more parameters:

- `--env_seed SEED` to specify the seed when building the environment for reproducibility. This is used
  to seed the grid2op environment.
- `--assistant_path PATH` to tell where to look for an "assistant". An assistant is "something" that can
  take some actions automatically on the powergrid. The "assistant path" must contain a package named
  `submission` (to be compliant with L2RPN competitions) that allows to import a function
  `make_agent(grid2op_environment, current_path) -> grid2op_agent` as in the L2RPN competitions. The
  assistant can be loaded after the interface is started.
- `--assistant_seed SEED` allows you to specify the seed used by your agent (for reproductibility)
  Depending on how you agent is coded, this might not work. This only calls `your_agent.seed(SEED)`.
  
For now it is not possible to change the `parameters` of the environment.

For example, a more complete command line would be:

```commandline
grid2game --dev --env_name C:\Users\USERNAME\LocalEnvironment --env_seed 42 --assistant_path C:\Users\USERNAME\Documents\L2RPN_Submissions\SubmissionName --assistant_seed 0
```

## Main Properties

By default, this app allows you to advance to the next step once, to advance in time until a game over (or an alarm, for environments supporting this feature, is raised by the assistant).

As opposed to a "regular" agent this also allows you to go "backward" in time. This is one of the reason why this is rather slow: at each steps the complete state of the grid, the action, the observation etc. are all stored. This "going backward" mode makes no sense for real time operation. But for real powergrid,
some operators perform grid "studies" in advance, using forecasts of future states. In this settings, the
main indicator of performance is "how long can the future grid stay in perfect working condition". In this
setting, to find the best "strategy" operator can explore different kind of actions at different steps
and thus it's important to go "backward" if the tested action is not satisfactory.

If no "assistant" is loaded, then doing the "action of the assistant" is equivalent to perform the "do nothing" action.

## Some restrictions

* This package is in early development, it might break and the name of its function and / layout can change.

* Once loaded, the environment cannot be changed.

## Known issues

As this package is still in "alpha" mode, there are some known issues.

One of the most impacting one is the difficulty, sometimes, to change the action manually. Action is not propagated correctly.

Another quite important one if the impossibility, in some cases to save the experiment in a correct way. The save experiments might not be the experiments displayed (this is due to the seeding of the environment).

It is also not very clear whether or not an "assistant" is loaded, especially on some screen size, where other informations might hide this one.
