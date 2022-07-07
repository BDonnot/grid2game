# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import os
import sys
import time

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from grid2game._utils import (add_callbacks_temporal,
                              setupLayout_temporal,
                              add_callbacks,
                              setupLayout,
                              add_callbacks_action_search,
                              setupLayout_action_search,
                              )
from grid2game.envs import Env
from grid2game.plot import PlotGrids, PlotTemporalSeries


class VizServer:
    SELF_LOOP_STOP = 0
    SELF_LOOP_GO = 1
    SELF_LOOP_GOFAST = 2

    GO_MODE = 11

    def __init__(self,
                 server,
                 build_args,
                 logger=None,
                 logging_level=None  # only used if logger is None
                 ):
        meta_tags = [
            {
                'name': 'grid2game',
                'content': 'Grid2Game a gamified platform to interact with grid2op environments'
            },
            {
                'http-equiv': 'X-UA-Compatible',
                'content': 'IE=edge'
            },
            {
                'name': 'viewport',
                'content': 'width=device-width, initial-scale=1.0'
            }
        ]
        external_stylesheets = [
            dbc.themes.BOOTSTRAP,
            {
                "rel": "stylesheet",
                "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
                "integrity": "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
                "crossorigin": "anonymous"
            },
        ]
        external_scripts = [
            {
                "src": "https://code.jquery.com/jquery-3.4.1.slim.min.js",
                "integrity": "sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n",
                "crossorigin": "anonymous"
            },
            {
                "src": "https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js",
                "integrity": "sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo",
                "crossorigin": "anonymous"
            },
            {
                "src": "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js",
                "integrity": "sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6",
                "crossorigin": "anonymous"
            }
        ]
        assets_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "assets")
        )

        # create the dash app
        self.my_app = dash.Dash(__name__,
                                server=server if server is not None else True,
                                meta_tags=meta_tags,
                                assets_folder=assets_dir,
                                external_stylesheets=external_stylesheets,
                                external_scripts=external_scripts)

        # Configure logging after dash initialization.
        # Otherwise dash is resetting logging level to INFO

        if not logging_level and build_args.logging_level:
            logging_level = build_args.logging_level

        if logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
            formatter = logging.Formatter('%(asctime)s - %(name)s %(filename)s.%(lineno)d | '
                                          '%(levelname)s:: %(message)s')
            fh = logging.FileHandler(f'{__name__}.log')
            fh.setFormatter(formatter)
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            if logging_level is not None:
                fh.setLevel(logging_level)
                ch.setLevel(logging_level)
                self.logger.setLevel(logging_level)
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
        else:
            self.logger = logger.getChild("VizServer")

        self.logger.info("Dash app initialized")

        # self.app.config.suppress_callback_exceptions = True

        # create the grid2op related things
        self.assistant_path = str(build_args.assistant_path)
        self.save_expe_path = ""

        if build_args._app_heroku:
            self.logger.info("Heorku mode used")
            self._app_heroku = True
        else:
            self._app_heroku = False

        # remember which substation is clicked on
        self._last_sub_id = None

        # read the right config
        g2op_config = self._make_glop_env_config(build_args)

        self.env = Env(build_args.env_name,
                       test=build_args.is_test,
                       assistant_path=self.assistant_path,
                       assistant_seed=int(build_args.assistant_seed) if build_args.assistant_seed is not None else None,
                       logger=self.logger,
                       config_dict=g2op_config)

        self._style_legal_info = {'color': 'red', "display": "flex", "alignItems": "center", "justifyContent": "center", 'display': 'none'}
        self._style_illegal_info = {'color': 'red', "display": "flex", "alignItems": "center", "justifyContent": "center"}

        if build_args.g2op_param is not None and build_args.g2op_param != "":
            self.env.set_params(build_args.g2op_param, reset=False)

        # seed part
        if build_args.env_seed is not None:
            self.env.seed(build_args.env_seed, reset=True)
        self.seed = None  # no seed are set through the UI yet

        # chronics part
        self.chronics_id = None  # no chronics are set through the UI yet

        self.logger.info("Environment initialized")
        self.plot_grids = PlotGrids(self.env.observation_space)
        self.fig_timeline = self.env.get_timeline_figure()

        self.plot_temporal = PlotTemporalSeries(self.env.env_tree)
        self.fig_load_gen = self.plot_temporal.fig_load_gen
        self.fig_line_cap = self.plot_temporal.fig_line_cap

        # internal members
        self.step_clicks = 0
        self.simulate_clicks = 0
        self.back_clicks = 0
        self.go_clicks = 1
        self.gofast_clicks = 0
        self.reset_clicks = 0
        self.nb_step_gofast = 12  # number of steps made in each frame for the "go_fast" mode
        self.time_refresh = 0.1  # in seconds (time at which the page will be refreshed)
        self.need_update_figures = False  # does the previous click on the button is the button
        # that makes it go until the end of the game ? If so i will need to upgrade, at the end of it, the
        # state of the grid

        # remembering the last step, that are not saved in the observation...
        self._last_step = 0
        self._last_max_step = 1
        self._last_done = False
        self._progress_color = "primary"

        # buttons layout
        self._button_shape = "btn btn-primary"
        self._go_button_shape = "btn btn-primary"  # "go" button
        self._gofast_button_shape = "btn btn-primary"  # "+XXX" button
        self._go_till_go_button_shape = "btn btn-primary"  # "end" button

        # ugly hack for the date time display
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

        # tools to plot
        self.plot_grids.init_figs(self.env.obs, self.env.sim_obs)
        self.real_time = self.plot_grids.figure_rt
        self.forecast = self.plot_grids.figure_forecat

        # initialize the layout
        self._layout_temporal = html.Div(setupLayout_temporal(self),
                                         id="all_temporal")
        self._layout_temporal_tab = dcc.Tab(label='Temporal view',
                                            value=f'tab-temporal-view',
                                            children=self._layout_temporal)

        self._layout_action_search = html.Div(setupLayout_action_search(self),
                                              id="all_action_search")
        self._layout_action_search_tab = dcc.Tab(label='Explore actions',
                                                 value='tab-explore-action',
                                                 children=self._layout_action_search)

        tmp_ = setupLayout(self,
                           self._layout_temporal_tab,
                           self._layout_action_search_tab)

        self.my_app.layout = tmp_

        add_callbacks_temporal(self.my_app, self)
        add_callbacks_action_search(self.my_app, self)
        add_callbacks(self.my_app, self)

        self.logger.info("Viz server initialized")

        # last node id (to not plot twice the same stuff to gain time)
        self._last_node_id = -1

        # last action taken
        self._last_action = "assistant"
        self._do_display_action = True
        self._dropdown_value = "assistant"

    def _make_glop_env_config(self, build_args):
        g2op_config = {}
        cont_ = True
        if build_args.g2op_config is not None and build_args.g2op_config != "":
            if not os.path.exists(build_args.g2op_config):
                msg = f"init: {build_args.g2op_config} does not exist"
                self.logger.error(msg)
                cont_ = False
            if not os.path.isfile(build_args.g2op_config):
                msg = f"init: {build_args.g2op_config} is not a file"
                self.logger.error(msg)
                cont_ = False
            if cont_:
                try:
                    cont_ = False
                    full_path = os.path.abspath(build_args.g2op_config)
                    base, fn = os.path.split(full_path)
                    fn, ext = os.path.splitext(fn)
                    sys.path.append(base)
                    import importlib
                    config_module = importlib.import_module(f"{fn}")
                    g2op_config = config_module.env_config
                    cont_ = True
                except ImportError as exc_:
                    msg = f"init: error {exc_} is not a file"
                    self.logger.error(msg)
        return g2op_config

    def run_server(self, debug=False):
        self.my_app.run_server(debug=debug)

    def change_nb_step_go_fast(self, nb_step_go_fast):
        if nb_step_go_fast is None:
            return dash.no_update,

        nb = int(nb_step_go_fast)
        self.nb_step_gofast = nb
        return f"+ {self.nb_step_gofast}",

    def unit_clicked(self, line_unit, line_side, load_unit, gen_unit, stor_unit,
                     trigger_rt_graph, trigger_for_graph):
        """handle the click to all button to change the units"""
        trigger_rt_graph = 0
        trigger_for_graph = 0
        # controls the panels of the main graph of the grid
        if line_unit != self.plot_grids.line_info:
            self.plot_grids.line_info = line_unit
            self.plot_grids.update_lines_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if line_side != self.plot_grids.line_side:
            self.plot_grids.line_side = line_side
            self.plot_grids.update_lines_side()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if load_unit != self.plot_grids.load_info:
            self.plot_grids.load_info = load_unit
            self.plot_grids.update_loads_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if gen_unit != self.plot_grids.gen_info:
            self.plot_grids.gen_info = gen_unit
            self.plot_grids.update_gens_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        if stor_unit != self.plot_grids.storage_info:
            self.plot_grids.storage_info = stor_unit
            self.plot_grids.update_storages_info()
            trigger_rt_graph = 1
            trigger_for_graph = 1
        return [trigger_rt_graph, trigger_for_graph]

    def _reset_action_to_assistant_if_not_prev(self):
        if self._last_action != "prev" :
            self._next_action_is_assistant()

    # handle the interaction with the grid2op environment
    def handle_act_on_env(
        self,
        step_butt,
        simulate_butt,
        back_butt,
        reset_butt,
        go_butt,
        gofast_clicks,
        until_game_over,
        untilgo_butt,
        self_loop,
        state_trigger_rt,
        state_trigger_for,
        state_trigger_self_loop,
        timer
    ):
        """
        dash do not make "synch" callbacks (two callbacks can be called at the same time),
        however, grid2op environments are not "thread safe": accessing them from different "thread"
        "coroutine" "process" is not a good idea.

        This function ensures that all functions related to the manipulation of the environment
        are done sequentially.

        see https://dash.plotly.com/advanced-callbacks, paragraph
        "Prevent Callback Execution Upon Initial Component Render"
        """
        # check which call backs triggered this calls
        # see https://dash.plotly.com/advanced-callbacks
        # section "Determining which Input has fired with dash.callback_context"
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            raise dash.exceptions.PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        display_new_state = 1
        something_clicked = True

        i_am_computing_state = {'display': 'block'}
        display_new_state = 0  # by default I am computing I do not update the graphs
        self._button_shape = "btn btn-secondary"  # by default buttons are "grey"
        self._gofast_button_shape = "btn btn-secondary"
        self._go_button_shape = "btn btn-secondary"
        self._go_till_go_button_shape = "btn btn-secondary"
        change_graph_title = dash.no_update
        update_progress_bar = 1
        check_issue = dash.no_update

        # now register the next computation to do, based on the button triggerd
        if button_id == "step-button":
            self.env.start_computation()
            self.env.next_computation = "step"
            self.env.next_computation_kwargs = {}
            self.need_update_figures = False
            check_issue = 1
        elif button_id == "go_till_game_over-button":
            self.env.start_computation()
            self.env.next_computation = "step_end"
            self.env.next_computation_kwargs = {}
            self.need_update_figures = True
            check_issue = 1
        elif button_id == "reset-button":
            self.env.start_computation()
            self.env.next_computation = "reset"
            self.env.next_computation_kwargs = {"chronics_id": self.chronics_id, "seed": self.seed}
            self.need_update_figures = False
            change_graph_title = 1
            self._next_action_is_assistant()
        elif button_id == "simulate-button":
            self.env.start_computation()
            self.env.next_computation = "simulate"
            self.env.next_computation_kwargs = {}
            self.need_update_figures = False
        elif button_id == "back-button":
            self.env.start_computation()
            self.env.next_computation = "back"
            self.env.next_computation_kwargs = {}
            self.need_update_figures = False
        elif button_id == "gofast-button":
            # this button is off now !
            self.env.start_computation()
            self.env.next_computation = "step_rec_fast"
            self.env.next_computation_kwargs = {"nb_step_gofast": self.nb_step_gofast}
            check_issue = 1
        elif button_id == "go-button":
            self.go_clicks += 1
            if self.go_clicks % 2:
                # i clicked on gofast an even number of times, i need to stop computation
                self.env.stop_computation()
                self._button_shape = "btn btn-primary"
                self._gofast_button_shape = "btn btn-primary"
            else:
                # i clicked on gofast an odd number of times, i need to start computation
                self.env.start_computation()
                self._button_shape = "btn btn-secondary"
                self._gofast_button_shape = "btn btn-secondary"
                check_issue = 1
            self.env.next_computation = "step_rec"
            self.env.next_computation_kwargs = {}
            self.need_update_figures = False
            display_new_state = 1  # in this mode, even though I am computing, I need to update the graphs live
        else:
            something_clicked = False

        if not self.env.needs_compute():
            # don't start the computation if not needed
            i_am_computing_state = {'display': 'none'}  # deactivate the "i am computing button"
            display_new_state = 1  # I am NOT computing I DO update the graphs
            self._button_shape = "btn btn-primary"
            self._gofast_button_shape = "btn btn-primary"
            self._go_button_shape = "btn btn-primary"
            self._go_till_go_button_shape = "btn btn-primary"

        in_go_mode = self.go_clicks % 2 == 0

        if not self.env.needs_compute() and self.need_update_figures and not something_clicked and not in_go_mode:
            # in this case, this should be the first call to this function after the "operate the grid until the
            # end" function is called
            # so i need to force update the figures
            display_new_state = 0
            self.need_update_figures = False
            # I need that to the proper update of the progress bar
            self._last_step = self.env.obs.current_step
            self._last_max_step = self.env.obs.max_step

            i_am_computing_state = {'display': 'none'}  # deactivate the "i am computing button"
            self._button_shape = "btn btn-primary"
            self._gofast_button_shape = "btn btn-primary"
            self._go_button_shape = "btn btn-primary"
            self._go_till_go_button_shape = "btn btn-primary"

        elif in_go_mode:
            # I have clicked on the "go" button, I need to "hack" everything to make sure proper buttons are set correctly
            # for this case
            display_new_state = type(self).GO_MODE
            i_am_computing_state = {'display': 'block'}
            self._go_button_shape = "btn btn-primary"

            self._go_till_go_button_shape = "btn btn-secondary"
            self._gofast_button_shape = "btn btn-secondary"
            self._button_shape = "btn btn-secondary"

        return [display_new_state,
                self._button_shape,
                self._button_shape,
                self._button_shape,
                self._button_shape,
                self._go_button_shape,
                self._gofast_button_shape,
                self._go_till_go_button_shape,
                i_am_computing_state,
                i_am_computing_state,
                change_graph_title,
                update_progress_bar,
                check_issue]

    def _wait_for_computing_over(self):
        i = 0
        while self.env.is_computing():
            time.sleep(0.1)
            i += 1
            if i >= 20:
                # in this case, the environment has not finished running for 2s, I stop here
                # in this case the user should probably call reset another time !
                raise dash.exceptions.PreventUpdate

    def check_issue(self, n1, n_clicks):
        # make sure the environment has nothing to compute
        while self.env.needs_compute():
            time.sleep(0.1)

        issues = self.env._current_issues
        if issues:
            len_issues = len(issues)
            if len_issues == 1:
                issue_text = f"There is {len_issues} issue: "
            else:
                issue_text = f"There are {len_issues} issues: "
            for issue in issues:
                issue_text += f"{issue}, "
            # Replace last ', ' by '.' to end the sentence
            issue_text = '.'.join(issue_text.rsplit(', ', 1))
            is_open = True
        else:
            issue_text = dash.no_update
            is_open = False

        return [is_open, issue_text]

    def change_graph_title(self, change_graph_title):
        # make sure that the environment has done computing
        self._wait_for_computing_over()

        # reset the elements !
        self.seed = None
        self.chronics_id = None
        chronics_name = None
        set_seed = None
        return [f"Scenario: {self.env.scenario_id()}", f"(seed: {self.env.glop_env.seed_used})", chronics_name, set_seed]

    def set_chronics(self, chronics):
        if chronics is not None:
            self.chronics_id = chronics
        return [1]

    def set_seed(self, seed):
        if seed is not None:
            self.seed = int(seed)
        return [1]

    def computation_wrapper(self, display_new_state, recompute_rt_from_timeline):
        # simulate a "state" of the application that depends on the computation
        if not self.env.is_computing():
            self.env.heavy_compute()

        if self.env.is_computing() and display_new_state != type(self).GO_MODE:
            # environment is computing I do not update anything
            raise dash.exceptions.PreventUpdate

        if display_new_state == 1 or display_new_state == type(self).GO_MODE:
            trigger_rt = 1
            trigger_for = 1

            # update the state only if needed
            if self.env.get_current_node_id() == self._last_node_id:
                # the state did not change, i do not update anything
                raise dash.exceptions.PreventUpdate
            else:
                self._last_node_id = self.env.get_current_node_id()
        else:
            trigger_rt = dash.no_update
            trigger_for = dash.no_update
        return [trigger_rt, trigger_for]

    # handle the layout
    def update_rt_fig(self, env_act):
        """the real time figures need to be updated"""
        if env_act is not None and env_act > 0:
            self.update_obs_fig()
            trigger_temporal_figs = 1
            trigger_rt_graph = 1
            trigger_for_graph = 1
        else:
            raise dash.exceptions.PreventUpdate

        if trigger_rt_graph == 1:
            self.fig_timeline = self.env.get_timeline_figure()

        update_progress_bar = 1
        return [trigger_temporal_figs,
                trigger_rt_graph,
                trigger_for_graph,
                self.fig_timeline,
                update_progress_bar]

    def update_progress_bar(self, from_act, from_figs):
        """update the progress bar"""
        # if from_act is None and from_figs is None:
            # raise dash.exceptions.PreventUpdate
        if self.env.env_tree.current_node is None:
            # A reset has just been called and the grid2op env is not reset yet
            self._progress_color = "primary"
            self._last_step = 0
            self._last_done = False
            self._last_max_step = max(self._last_max_step, 1)  # prevent possible division by 0.
        else:
            # scenario progress bar
            self._progress_color = "primary"
            if not self.env.is_done:
                # if from_act == 1:
                #     self._last_step = max(self.env.obs.current_step, self._last_step)
                #     self._last_max_step = max(self.env.obs.max_step, self._last_max_step)
                # elif from_figs == 1:
                self._last_step = self.env.obs.current_step
                self._last_max_step = self.env.obs.max_step
                self._last_done = False
            else:
                self._last_step = self.env.obs.current_step
                self._last_max_step = self.env.obs.max_step
                # if not self._last_done:
                #     self._last_done = True
                #     if self._last_step != self._last_max_step:
                #         # fail to run the scenario till the end
                #         self._last_step += 1
                if self._last_step != self._last_max_step:
                    # fail to run the scenario till the end
                    self._progress_color = "danger"
                else:
                    # no game over, until the end of the scenario
                    self._progress_color = "success"

        progress_pct = 100. * self._last_step / self._last_max_step
        progress_label = f"{self._last_step} / {self._last_max_step}"
        return [progress_pct,
                progress_label,
                self._progress_color]

    def update_simulated_fig(self, env_act):
        """the simulate figures need to updated"""
        if env_act is not None and env_act > 0:
            trigger_for_graph = 1
            self.plot_grids.update_forecat(self.env.sim_obs, self.env)
            self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"
        else:
            raise dash.exceptions.PreventUpdate
        return [trigger_for_graph]

    def show_temporal_graphs(self, show_temporal_graph):
        """handles the action that displays (or not) the time series graphs"""
        if (show_temporal_graph is None or show_temporal_graph.empty()):
            raise dash.exceptions.PreventUpdate
        return [1]

    # define the style of the temporal graph, whether is how it or not
    def show_hide_tempo_graph(self, do_i_show):
        display_mode = {'display': 'none'}
        if do_i_show:
            # i should display the figure
            display_mode = {'display': 'block'}
            self.plot_temporal.update_layout_height()  # otherwise figures shrink when trigger is called
        return [display_mode, 1]

    # end point of the trigger stuff: what is displayed on the page !
    def update_temporal_figs(self, figrt_trigger, showhide_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (showhide_trigger is None or showhide_trigger == 0):
            raise dash.exceptions.PreventUpdate
        self.fig_load_gen, self.fig_line_cap = self.plot_temporal.update_trace(self.env, self.env.env_tree)
        return [self.fig_load_gen, self.fig_line_cap]

    def update_rt_graph_figs(self, figrt_trigger, unit_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (unit_trigger is None or unit_trigger == 0):
            # nothing really triggered this call
            raise dash.exceptions.PreventUpdate
        self._wait_for_computing_over()
        if self.env.env_tree.current_node.prev_action_is_illegal:
            is_illegal = 1
        else:
            is_illegal = 0
        return [self.real_time,  self.rt_datetime, is_illegal]

    def update_if_rt_illegal(self, trigger_rt_extra_info):
        if trigger_rt_extra_info:
            pass

    def update_for_graph_figs(self, figrt_trigger, figfor_trigger, unit_trigger):
        if (figrt_trigger is None or figrt_trigger == 0) and \
                (figfor_trigger is None or figfor_trigger == 0) and \
                (unit_trigger is None or unit_trigger == 0):
            # nothing really triggered this call
            raise dash.exceptions.PreventUpdate
        self._wait_for_computing_over()
        if self.env.is_assistant_illegal():
            is_illegal = 1
        else:
            is_illegal = 0
        return [self.forecast, self.for_datetime, is_illegal]

    def tell_illegal_rt(self, is_illegal):
        if is_illegal == 1:
            res = self._style_illegal_info
        else:
            res = self._style_legal_info
        return [res]

    def tell_illegal_for(self, is_illegal):
        if is_illegal == 1:
            res = self._style_illegal_info
        else:
            res = self._style_legal_info
        return [res]

    # auxiliary functions
    def update_obs_fig(self):
        self.plot_grids.update_rt(self.env.obs, self.env)
        self.rt_datetime = f"{self.env.obs.get_time_stamp():%Y-%m-%d %H:%M}"
        self.plot_grids.update_forecat(self.env.sim_obs, self.env)
        self.for_datetime = f"{self.env.sim_obs.get_time_stamp():%Y-%m-%d %H:%M}"

    def _next_action_is_manual(self):
        self.env.next_action_copy()
        self.env.next_action_is_manual()
        self._last_action = "manual"
        self._do_display_action = True
        self._dropdown_value = "manual"

    def _next_action_is_assistant(self):
        self.env.next_action_is_assistant()
        self._last_action = "assistant"
        self._do_display_action = True
        self._dropdown_value = "assistant"

    def display_action_fun(self,
                           which_action_button,
                           do_display,
                           gen_redisp_curtail,
                           gen_id,
                           redisp,
                           stor_id, storage_p,
                           line_id, line_status,
                           sub_id, clicked_sub_fig):
        """
        modify the action taken based on the inputs,
        then displays the action (as text)
        """
        # TODO handle better the action (this is ugly to access self.env._current_action from here)

        ctx = dash.callback_context
        dropdown_value = self._last_action
        update_substation_layout_clicked_from_sub = 0
        if not ctx.triggered:
            # no click have been made yet
            return [f"{self.env.current_action}", dropdown_value, update_substation_layout_clicked_from_sub]
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == "which_action_button":
            # the "base action" has been modified, so i need to change it here
            if which_action_button == "dn":
                self.env.next_action_is_dn()
                self._last_action = "dn"
                self._do_display_action = False
                self._dropdown_value = "dn"
            elif which_action_button == "assistant":
                self._next_action_is_assistant()
            elif which_action_button == "prev":
                self.env.next_action_is_previous()
                self._last_action = "prev"
                self._do_display_action = False
                self._dropdown_value = "prev"
            elif which_action_button == "manual":
                self._next_action_is_manual()
            else:
                # nothing is done
                pass
            res = [f"{self.env.current_action}", dropdown_value, update_substation_layout_clicked_from_sub]
            return res

        if not self._do_display_action:
            # i should not display the action
            res = [f"{self.env.current_action}", dropdown_value, update_substation_layout_clicked_from_sub]
            return res

        # i need to display the action
        # self._last_action = "manual"
        # dropdown_value = "manual"
        # self.env.next_action_is_manual()
        is_modif = False
        if gen_id != "":
            try:
                gen_id_int = int(gen_id)
                if self.env.glop_env.gen_renewable[gen_id_int]:
                    self.env._current_action.curtail_mw = [(int(gen_id), float(redisp))]

                else:
                    self.env._current_action.redispatch = [(int(gen_id), float(redisp))]
                is_modif = True
            except Exception as exc_:
                # either initialization of something else
                self.logger.error(f"Error in display_action_fun: {exc_}")
                pass
        if stor_id != "":
            self.env._current_action.storage_p = [(int(stor_id), float(storage_p))]
            is_modif = True
        if line_id != "" and line_status is not None:
            self.env._current_action.line_set_status = [(int(line_id), int(line_status))]
            is_modif = True
        if sub_id != "":
            is_modif = True
            update_substation_layout_clicked_from_sub = 1
            if clicked_sub_fig is not None:
                # i modified a substation topology
                obj_id, new_bus = self.plot_grids.get_object_clicked_sub(clicked_sub_fig)
                if obj_id is not None:
                    self.env._current_action.set_bus = [(obj_id, new_bus)]

        if not is_modif:
            raise dash.exceptions.PreventUpdate

        # TODO optim here to save that if not needed because nothing has changed
        res = [f"{self.env.current_action}", self._dropdown_value, update_substation_layout_clicked_from_sub]
        return res

    def display_grid_substation(self, update_substation_layout_clicked_from_sub, update_substation_layout_clicked_from_grid):
        """update the figure of the substation (when zoomed in)"""
        if update_substation_layout_clicked_from_sub != 1 and update_substation_layout_clicked_from_grid != 1:
            raise dash.exceptions.PreventUpdate
        if update_substation_layout_clicked_from_sub is None and update_substation_layout_clicked_from_grid is None:
            raise dash.exceptions.PreventUpdate

        # update "in real time" the topology of the substation (https://github.com/BDonnot/grid2game/issues/36)
        if self._last_sub_id is None:
            self.logger.error("display_click_data: Unable to update the substatin plot: no know last substation id")
            raise dash.exceptions.PreventUpdate
        sub_res = self.plot_grids.update_sub_figure(self.env._current_action, self._last_sub_id)
        return [sub_res[-1]]

    def display_click_data(self,
                           clickData,
                           back_clicked,
                           step_clicked,
                           simulate_clicked,
                           go_clicked,
                           gofast_clicked,
                           until_gameover):
        """display the interaction window when the real time graph is clicked on"""
        do_display_action = 0
        gen_redisp_curtail = ""
        style_gen_input = {'display': 'none'}
        gen_id_clicked = ""
        gen_res = ["", -1., 1., 0., "gen_p", "target_disp", "actual_disp"]

        style_storage_input = {'display': 'none'}
        storage_id_clicked = ""
        storage_res = ["", -1., 1., 0., "storage_power", "storage_capaticy"]

        style_line_input = {'display': 'none'}
        line_id_clicked = ""
        line_res = ["", 0, "flow"]

        style_sub_input = {'display': 'none'}
        sub_id_clicked = ""
        sub_res = ["", self.plot_grids.sub_fig]
        update_substation_layout_clicked_from_grid = 0

        # check which call backs triggered this calls
        # see https://dash.plotly.com/advanced-callbacks
        # section "Determining which Input has fired with dash.callback_context"
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            # so no action displayed
            return [do_display_action,
                    style_gen_input, gen_redisp_curtail, gen_id_clicked, *gen_res,
                    style_storage_input, storage_id_clicked, *storage_res,
                    style_line_input, line_id_clicked, *line_res,
                    style_sub_input, sub_id_clicked, *sub_res[:-1],
                    update_substation_layout_clicked_from_grid
                    ]
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # https://stackoverflow.com/questions/50213761/changing-visibility-of-a-dash-component-by-updating-other-component
        if clickData is None:
            # i never clicked on any data
            do_display_action = 0
            self._last_sub_id = None
        elif button_id == "step-button" or button_id == "simulate-button" or \
                button_id == "go-button" or button_id == "gofast-button" or\
                button_id == "back-button":
            # i never clicked on simulate, step, go, gofast or back
            do_display_action = 0
            self._last_sub_id = None
        else:
            # I clicked on the graph of the grid
            self._last_sub_id = None
            obj_type, obj_id, res_type = self.plot_grids.get_object_clicked(clickData)
            if obj_type == "gen":
                gen_redisp_curtail = "Curtail (MW)" if self.env.glop_env.gen_renewable[obj_id] else "Redispatch"
                gen_id_clicked = f"{obj_id}"
                style_gen_input = {'display': 'inline-block'}
                gen_res = res_type
                do_display_action = 1
            elif obj_type == "stor":
                storage_id_clicked = f"{obj_id}"
                style_storage_input = {'display': 'inline-block'}
                storage_res = res_type
                do_display_action = 1
            elif obj_type == "line":
                line_id_clicked = f"{obj_id}"
                style_line_input = {'display': 'inline-block'}
                line_res = res_type
                do_display_action = 1
            elif obj_type == "sub":
                sub_id_clicked = f"{obj_id}"
                style_sub_input = {'display': 'inline-block'}
                sub_res = res_type
                do_display_action = 1
                # remember that for next time
                self._last_sub_id = obj_id
                update_substation_layout_clicked_from_grid = 1
            else:
                raise dash.exceptions.PreventUpdate
            # self._next_action_is_manual()
        return [do_display_action,
                style_gen_input, gen_redisp_curtail, gen_id_clicked, *gen_res,
                style_storage_input, storage_id_clicked, *storage_res,
                style_line_input, line_id_clicked, *line_res,
                style_sub_input, sub_id_clicked, *sub_res[:-1],
                update_substation_layout_clicked_from_grid
                ]

    def format_path(self, path):
        """just output the name of the submission instead of its whole path"""
        try:
            base, res = os.path.split(path)
            return res.strip()
        except Exception as exc_:
            return path

    def load_assistant(self, trigger_load, assistant_path):
        """loads an assistant and display the right things"""
        loader_state = ""
        if assistant_path is None:
            raise dash.exceptions.PreventUpdate
        self.assistant_path = assistant_path.rstrip().lstrip()
        try:
            properly_loaded = self.env.load_assistant(self.assistant_path)
        except Exception as exc_:
            self.logger.error(f"Error in load_assistant: {exc_}")
            return [f"❌ {exc_}", dash.no_update, loader_state]
        clear = 0
        if properly_loaded:
            res = self.format_path(os.path.abspath(self.assistant_path))
            res = f"🤖 {res}"
            clear = 1
        else:
            res = ""
        return [res, clear, loader_state]

    def clear_loading(self, need_clearing):
        """once an assistant has been """
        if need_clearing == 0:
            raise dash.exceptions.PreventUpdate
        return [""]

    def save_expe(self, button, save_expe_path):
        """
        This callback save the experiment using a grid2op runner.

        work in progress !

        TODO: reuse the computation of the environment instead of creating a runner for such purpose !
        """
        loader_state = ""
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            raise dash.exceptions.PreventUpdate

        if self.env.is_computing():
            # cannot save while an experiment is running
            msg_ = "environment is still computing"
            self.logger.info(f"save_expe: {msg_}")
            return [f"⌛ {msg_}", loader_state]

        if save_expe_path is None:
            msg_ = "invalid path (None)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}", loader_state]

        self.save_expe_path = save_expe_path.rstrip().lstrip()
        if not os.path.exists(self.save_expe_path):
            msg_ = "invalid path (does not exists)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}", loader_state]
        if not os.path.isdir(self.save_expe_path):
            msg_ = "invalid path (not a directory)"
            self.logger.info(f"save_expe: {msg_}")
            return [f"❌ {msg_}", loader_state]
        self.logger.info(f"saving experiment in {self.save_expe_path}")
        self.env.start_computation()  # prevent other type of computation
        try:
            env = self.env.glop_env.copy()
            nb_step = self.env.obs.current_step
            chro_id = env.chronics_handler.get_id()
            from grid2op.Agent import FromActionsListAgent
            from grid2op.Runner import Runner
            list_action = self.env.get_current_action_list()
            agent = FromActionsListAgent(env.action_space, list_action)
            dict_ = env.get_params_for_runner()
            if "logger" in dict_:
                # don't use the logger of the grid2op environment
                del dict_["logger"]
            runner = Runner(**dict_,
                            agentClass=None,
                            agentInstance=agent,
                            logger=self.logger,
                            )
            runner.run(nb_episode=1,
                       path_save=self.save_expe_path,
                       episode_id=[chro_id],
                       max_iter=max(nb_step + 1, 2),
                       env_seeds=[self.env.glop_env.seed_used],  # TODO. in case of "reset" this might not work
                       # agent_seeds=[self.], TODO... This might require deep rework of this function !
                       pbar=True)
            res = f"✅ saved in \"{self.save_expe_path}\""
        except Exception as exc_:
            self.logger.error(f"save_expe exception while trying to save the experiment: {exc_}")
            res = f"❌ Something went wrong during the saving of the experiment. Error: {exc_}"
        finally:
            # ensure I stop the computation that i fake to start here
            self.env.stop_computation()  # prevent other type of computation
        return [res, loader_state]

    def timeline_set_time(self, time_line_graph_clicked):
        if self.env.is_computing():
            # nothing is updated if i am doing a computation
            raise dash.exceptions.PreventUpdate

        if time_line_graph_clicked is None:
            # I did no click on anything
            raise dash.exceptions.PreventUpdate

        res = self.env.handle_click_timeline(time_line_graph_clicked)
        self.need_update_figures = True  # hack to have the progress bar properly recomputed
        return [res]

    def tab_content_display(self, tab):
        res = [self._layout_temporal]

        if tab == 'tab-temporal-view':
            self.need_update_figures = True
            return [self._layout_temporal]
        elif tab == 'tab-explore-action':
            self.need_update_figures = True
            return [self._layout_action_search]
        else:
            msg_ = f"Unknown tab {tab}"
            self.logger.error(msg_)
        return res

    def _aux_tab_as_retrieve_updated_figs(self):
        progress_pct = 100. * self._last_step / self._last_max_step
        progress_label = f"{self._last_step} / {self._last_max_step}"
        self.fig_timeline = self.env.get_timeline_figure()
        self.update_obs_fig()

        pbar_value = progress_pct
        pbar_label = progress_label
        pbar_color = self._progress_color
        fig_timeline = self.fig_timeline
        dt_label = self.rt_datetime
        fig_rt = self.real_time
        return (pbar_value, pbar_label, pbar_color, fig_timeline,
                dt_label, fig_rt)

    def main_action_search(self,
                           refresh_button,
                           explore_butt_pressed,
                           timer):
        ctx = dash.callback_context
        if not ctx.triggered:
            # no click have been made yet
            raise dash.exceptions.PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        something_clicked = True

        # TODO button color here too !
        i_am_computing_state = {'display': 'block'}
        pbar_value = dash.no_update
        pbar_label = dash.no_update
        pbar_color = dash.no_update
        fig_timeline = dash.no_update
        dt_label = dash.no_update
        fig_rt = dash.no_update
        start_computation = 1

        if button_id == "refresh-button_as":
            # (pbar_value, pbar_label, pbar_color, fig_timeline,
            #     dt_label, fig_rt) = self._aux_tab_as_retrieve_updated_figs()
            start_computation = dash.no_update
            # hack for it to resynch everything
            self.need_update_figures = True
        elif button_id == "explore-button_as":
            self.env.next_computation = "explore"
            self.need_update_figures = True
            self.env.start_computation()
        else:
            something_clicked = False

        if not self.env.needs_compute():
            # don't start the computation if not needed
            i_am_computing_state = {'display': 'none'}  # deactivate the "i am computing button"
            start_computation = dash.no_update  # I am NOT computing I DO update the graphs

        if not self.env.needs_compute() and self.need_update_figures and not something_clicked:
            # in this case, this should be the last call to this function after the "explore"
            # function is finished
            # so i need to force update the figures
            start_computation = dash.no_update
            self.need_update_figures = False
            i_am_computing_state = {'display': 'none'}  # deactivate the "i am computing button"

            (pbar_value, pbar_label, pbar_color, fig_timeline,
                dt_label, fig_rt) = self._aux_tab_as_retrieve_updated_figs()

        return [start_computation,
                pbar_value,
                pbar_label,
                pbar_color,
                fig_timeline,
                dt_label,
                fig_rt,
                1,
                i_am_computing_state,
                i_am_computing_state]
