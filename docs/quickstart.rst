Getting started
===================================

Install grid2game
------------------------------------

As of writing, the only possible way to install grid2game is to install it with pip from the github repository.

It can be achieved with:

.. code-block:: none

    pip install git+https://github.com/bdonnot/grid2game.git

.. warning::
    We more than recommend to use a dedicated virtual environment when installing grid2game. Indeed it depends on
    different packages and we found that it works much better inside a python virtual environment.

    On linux / macOS you might create one with: `python3 -m virtualenv venv` [need to be done once]
    and then, each time you want to use grid2game, you can activate it with:  `source venv/bin/activate`

    On windows 10 (and I suppose windows 11 too, but with Microsoft who knows...), 
    you can create one with: `py -m virtualenv venv` [need to be done once]
    and then, each time you want to use grid2game, you can activate it with:  `.\venv\Scripts\activate.ps1`

.. note::
    We highly recommend you to use lightsim2grid backend if you want to use grid2game. Otherwise the application
    will be way less responsive, because the computation of flows will take a lot of time.


Main concepts
---------------------------
TODO

Start Using grid2game
---------------------------

Once install, you will need to start a grid2game server and then interact with it from a web browser (we
tested mozilla firefox and google chrome).

Start the server
~~~~~~~~~~~~~~~~~~~~~~

For that you need to run, in a command line (when the virtual environment is activated) the command:

.. code-block:: none
    
    grid2game --env_name educ_case14_storage --is_test

You can specify it at your own will with:

- `--dev` specifies that the dash server will run in "dev" mode, we recommend you to use it
- `--env_name educ_case14_storage` specifies that the application will run the `educ_case14_storage`
  environment. You can use any environment available on your machine or that can be made with
  a pytho command like `env = grid2op.make(env_name)`
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
- `--g2op_param ./g2op_params.json` set of parameters used to update the environment (this should be compatible 
  with `param.init_from_json` from grid2op)
- `--g2op_config ./g2op_env_customization.py` how to configure the grid2op environment, this file should contain
  a dictionnary named `env_config` and it will be used to initialize the grid2Op environment with : 
  `env.make(..., **env_config)` 

Interact with it
~~~~~~~~~~~~~~~~~~~~~~

TODO

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`