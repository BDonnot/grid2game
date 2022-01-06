# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.
import os
import numpy as np
import copy
import time

import grid2op
from grid2op.Action import PlayableAction
from grid2op.Backend import PandaPowerBackend
from grid2op.Exceptions import NoForecastAvailable

try:
    from lightsim2grid import LightSimBackend
    bkClass = LightSimBackend
except ImportError:
    # TODO: logger here
    bkClass = PandaPowerBackend


from grid2game.agents import load_assistant
from grid2game.envs.computeWrapper import ComputeWrapper
from grid2game.tree import EnvTree


class Env(ComputeWrapper):
    """
    wrapper of a grid2op environment. What it does compared to a standard grid2op env ? Store everything
    at every steps to be able to navigate back and forth in the past or in the future.
    """
    ASSISTANT = 0
    DO_NOTHING = 1
    LIKE_PREVIOUS = 2
    MANUAL = 3

    def __init__(self,
                 env_name,
                 assistant_path=None,
                 assistant_seed=0,
                 logger=None,
                 config_dict=None,
                 **kwargs):
        ComputeWrapper.__init__(self)

        if logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger.getChild("Env")

        if config_dict is None:
            config_dict = {}

        # TODO some configuration here
        self.glop_env = grid2op.make(env_name,
                                     backend=bkClass(),
                                     action_class=PlayableAction,
                                     logger=self.logger,
                                     **config_dict,
                                     **kwargs)
        self.logger.info("Grid2op environment initialized")
        self.do_stop_if_alarm = True  # I stop if an alarm is raised by the assistant, by default
        # TODO have a way to change self.do_stop_if_alarm easily from the UI

        self.env_tree = EnvTree()
        self._current_action = None
        self._sim_obs = None
        self._sim_reward = None
        self._sim_done = None
        self._sim_info = None

        # define variables
        self._should_display = True

        # assistant part
        self.assistant_path = assistant_path
        self.assistant_seed = assistant_seed
        self.next_action_from = self.ASSISTANT
        self._assistant_action = None  # not to recompute it each time
        self.assistant = None
        self._assistant_seed = assistant_seed
        self.load_assistant(assistant_path)

        self.init_state()

        # to control which action will be done when
        self.next_computation = None
        self.next_computation_kwargs = {}

    def prevent_display(self):
        self._should_display = False

    def authorize_dispay(self):
        self._should_display = True

    def do_i_display(self):
        return self._should_display

    def get_timeline_figure(self):
        return self.env_tree.plot_plotly()

    def get_current_node_id(self):
        return self.env_tree.current_node.id

    def load_assistant(self, assistant_path):
        self.logger.info(f"attempt to load assistant with path : \"{assistant_path}\"")
        has_been_loaded = False
        if assistant_path != "" and assistant_path not in {"unload", "\"", "\"\""}:
            # a real path has been set up
            tmp = load_assistant(assistant_path, self._assistant_seed, self.glop_env.copy(), logger=self.logger)
            if tmp is not None:
                # it means the agent has been loaded
                self.assistant = tmp
                has_been_loaded = True
            else:
                # TODO do something smart to warn the error.
                pass
        else:
            # cancel the assistant
            from grid2op.Agent import DoNothingAgent  # TODO do nothing here
            self.assistant = DoNothingAgent(self.glop_env.action_space)
            if self._assistant_seed is not None:
                self.assistant.seed(int(self._assistant_seed))

        if has_been_loaded:
            # # TODO do i "change the past" ?
            pass
            # for step_id in range(len(self.past_envs)):
            #     _current_action, \
            #     _assistant_action, \
            #     _obs, _reward, _done, _info, \
            #     glop_env = self.past_envs[step_id]
            #     _assistant_action = self.assistant.act(_obs, _reward, _done)
            #     self.past_envs[step_id] = (_current_action,
            #                                _assistant_action,
            #                                _obs, _reward, _done, _info,
            #                                glop_env)
        self.logger.info(f"assistant loaded with class {type(self.assistant)}")
        return has_been_loaded

    def do_computation(self):
        if self.next_computation is None:
            return

        if self.next_computation == "load_assistant":
            self.stop_computation()  # this is a "one time" call
            return self.load_assistant(**self.next_computation_kwargs)
        elif self.next_computation == "seed":
            self.stop_computation()  # this is a "one time" call
            return self.seed(**self.next_computation_kwargs)
        elif self.next_computation == "step":
            self.stop_computation()  # this is a "one time" call
            return self.step(**self.next_computation_kwargs)
        elif self.next_computation == "step_rec":
            res = self.step()
            obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
            if self._stop_if_alarm(obs):
                # I stop the computation if the agent sends an alarm
                self.logger.info("step_rec: An alarm is raised, I stop")
                self.stop_computation()
            return res
        elif self.next_computation == "step_rec_fast":
            # currently not used !
            res = None
            for i in range(int(self.next_computation_kwargs["nb_step_gofast"])):
                res = self.step()
                obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
                if self._stop_if_alarm(obs):
                    self.logger.info("step_rec_fast: An alarm is raised, I stop")
                    break
            self.stop_computation()  # this is a "one time" call
            return res
        elif self.next_computation == "step_end":
            res = None
            self.prevent_display()
            obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
            while not done:
                res = self.step()
                obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
                if self._stop_if_alarm(obs):
                    self.logger.info("step_end: An alarm is raised, I stop")
                    break
            self.stop_computation()  # this is a "one time" call
            self.authorize_dispay()
            return res
        elif self.next_computation == "choose_next_action":
            self.stop_computation()  # this is a "one time" call
            return self.choose_next_action()
        elif self.next_computation == "simulate":
            self.stop_computation()  # this is a "one time" call
            return self.simulate(**self.next_computation_kwargs)
        elif self.next_computation == "back":
            self.stop_computation()  # this is a "one time" call
            return self.back()
        elif self.next_computation == "reset":
            self.stop_computation()  # this is a "one time" call
            return self.reset()
        else:
            msg_ = f"Unknown method to call: {self.next_computation = }"
            self.logger.error(msg_)
            raise RuntimeError(msg_)
        # elif self.next_computation == "next_action_is_dn":  # TODO is this really public api ?
        #     self.stop_computation()  # this is a "one time" call
        #     return self.next_action_is_dn()
        # elif self.next_computation == "next_action_is_previous":  # TODO is this really public api ?
        #     self.stop_computation()  # this is a "one time" call
        #     return self.next_action_is_previous()
        # elif self.next_computation == "next_action_is_assistant":  # TODO is this really public api ?
        #     self.stop_computation()  # this is a "one time" call
        #     return self.next_action_is_assistant()
        # elif self.next_computation == "take_last_action":  # TODO is this really public api ?
        #     self.stop_computation()  # this is a "one time" call
        #     return self.take_last_action()

    def _stop_if_alarm(self, obs):
        if self.do_stop_if_alarm:
            if np.any(obs.time_since_last_alarm == 0):
                return True
        return False

    @property
    def action_space(self):
        return self.glop_env.action_space

    @property
    def observation_space(self):
        return self.glop_env.observation_space

    @property
    def obs(self):
        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
        return obs

    @property
    def current_action(self):
        return self._current_action

    @property
    def sim_obs(self):
        return self._sim_obs

    @property
    def is_done(self):
        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
        return done

    def take_last_action(self):
        """take the same action as last time"""
        # if self.past_envs:
        #     self._current_action = self.past_envs[-1][0]
        self._current_action = self.env_tree.get_last_action()

    def set_params(self, params_path, reset=False):
        """set the environment parameters"""
        self.logger.info(f"Updating the environment parameters.")
        if not os.path.exists(params_path):
            msg = f"set_params: {params_path} does not exists"
            self.logger.error(msg)
            raise RuntimeError(msg)
        if not os.path.isfile(params_path):
            msg = f"set_params: {params_path} is not a file"
            self.logger.error(msg)
            raise RuntimeError(msg)

        current_param = self.glop_env.parameters
        current_param.init_from_json(params_path)
        self.glop_env.change_parameters(current_param)
        self.glop_env.change_forecast_parameters(current_param)
        if reset:
            self.logger.info(f"set_params: resetting the environment")
            self.init_state()

    def seed(self, seed, reset=True):
        """seed and reset the environment"""
        self.logger.info(f"Setting env seed {seed} and resetting the environment.")
        seeds = self.glop_env.seed(seed)
        if reset:
            self.logger.info(f"seed: resetting the environment")
            self.init_state()
        return seeds

    def step(self, action=None):
        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
        if done:
            self.stop_computation()
            obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
            return obs, reward, done, info

        if action is None:
            action = self._current_action
        else:
            # TODO is this correct ? I never really tested that
            self._current_action = action

        self.env_tree.make_step(assistant=self.assistant, chosen_action=action)
        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()

        if obs.time_since_last_alarm == 0:
            self.logger.info("step: The assistant raised an alarm !")
            self.stop_computation()

        if not done:
            self.choose_next_action()
            self.logger.info("step: done is False")
            try:
                self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = obs.simulate(self._current_action)
            except NoForecastAvailable:
                self.logger.warn("step: no forecast seems to be available for the current observation.")
                pass
        else:
            self._sim_done = True
            self._sim_reward = self.glop_env.reward_range[0]
            self._sim_info = {}
            self._sim_obs.set_game_over(self.glop_env)
        return obs, reward, done, info

    def choose_next_action(self):
        self._assistant_action = None
        if self.next_action_from == self.ASSISTANT:
            obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
            self._assistant_action = self.assistant.act(obs, reward, done)
            self._current_action = copy.deepcopy(self._assistant_action)
        elif self.next_action_from == self.LIKE_PREVIOUS or self.next_action_from == self.MANUAL:
            # next action should be like the previous one or manually set
            self._current_action = copy.deepcopy(self._current_action)
        elif self.next_action_from == self.DO_NOTHING:
            self._current_action = self.glop_env.action_space()
        else:
            raise RuntimeError("Unsupported next action")

    def simulate(self, action=None):
        if action is None:
            action = self._current_action

        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
        self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = obs.simulate(action)
        return self._sim_obs, self._sim_obs, self._sim_reward, self._sim_done, self._sim_info

    def back(self):
        self.env_tree.back_one_step()

    def reset(self):
        self.init_state()

    def init_state(self):
        self.env_tree.clear()
        obs = self.glop_env.reset()            
        self.env_tree.root(assistant=self.assistant, obs=obs, env=self.glop_env)

        self._current_action = self.glop_env.action_space()
        if self.assistant is not None:
            self.next_action_is_assistant()
        obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
        self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = obs.simulate(self.current_action)

    def next_action_is_dn(self):
        """or do nothing if first step"""
        if self.next_action_from == self.DO_NOTHING:
            return
        self.next_action_from = self.DO_NOTHING
        self._current_action = self.glop_env.action_space()

    def next_action_is_previous(self):
        """or do nothing if first step"""
        if self.next_action_from == self.LIKE_PREVIOUS:
            return
        self.next_action_from = self.LIKE_PREVIOUS
        self._current_action = self.env_tree.get_last_action()

    def next_action_is_assistant(self):
        """the next action is chosen to be given by the assistant"""
        if self.next_action_from == self.ASSISTANT:
            return

        self.next_action_from = self.ASSISTANT
        if self._assistant_action is None:
            # self._assistant_action = self.glop_env.action_space.sample()
            obs, reward, done, info = self.env_tree.current_node.get_obs_rewar_done_info()
            self._assistant_action = self.assistant.act(obs, reward, done)
        self._current_action = copy.deepcopy(self._assistant_action)

    def next_action_is_manual(self):
        """the next action is manually selected"""
        if self.next_action_from == self.MANUAL:
            return
        self.next_action_from = self.MANUAL
        self._current_action = copy.deepcopy(self._current_action)

    def next_action_copy(self):
        """something has selected an action, i need to copy it not to erase it first !"""
        self._current_action = copy.deepcopy(self._current_action)

    def handle_click_timeline(self, time_line_graph_clcked) -> int:
        """handles the interaction from the timeline"""
        if "points" not in time_line_graph_clcked:
            return 0
        self.is_computing()
        res = self.env_tree.move_from_click(time_line_graph_clcked)
        self._current_action = copy.deepcopy(self.env_tree.get_last_action())
        self.stop_computation()  # this is a "one time" call
        return res

    def get_current_action_list(self):
        """return the list of actions from the current point in the tree up to the root"""
        return self.env_tree.get_current_action_list()
