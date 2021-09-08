# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import warnings
import numpy as np
import copy
import time

import grid2op
from grid2op.Action import PlayableAction
from grid2op.Backend import PandaPowerBackend

try:
    from lightsim2grid import LightSimBackend
    bkClass = LightSimBackend
except ImportError:
    # TODO: logger here
    bkClass = PandaPowerBackend


from grid2game.agents import load_assistant
from grid2game.envs.computeWrapper import ComputeWrapper


class Env(ComputeWrapper):
    """
    wrapper of a grid2op environment. What it does compared to a standard grid2op env ? Store everything
    at every steps to be able to navigate back and forth in the past or in the future.
    """
    ASSISTANT = 0
    DO_NOTHING = 1
    LIKE_PREVIOUS = 2

    def __init__(self,
                 env_name,
                 assistant_path=None,
                 assistant_seed=0,
                 **kwargs):
        ComputeWrapper.__init__(self)

        # TODO some configuration here
        self.glop_env = grid2op.make(env_name,
                                     backend=bkClass(),
                                     action_class=PlayableAction,
                                     **kwargs)

        # define variables
        self._obs = None
        self.past_envs = []
        self._current_action = None
        self._sim_obs = None
        self._sim_reward = None
        self._sim_done = None
        self._sim_info = None
        self._reward = None
        self._done = None
        self._info = None

        # todo have that in another class
        self._sum_load = None
        self._max_line_flow = None
        self._secondmax_line_flow = None
        self._thirdmax_line_flow = None
        self._sum_solar = None
        self._sum_wind = None
        self._sum_thermal = None
        self._sum_hydro = None
        self._sum_nuclear = None
        self._datetimes = None

        # assistant part
        self.assistant_path = assistant_path
        self.assistant_seed = assistant_seed
        self.next_action_from = self.ASSISTANT
        self._assistant_action = None  # not to recompute it each time
        self.assistant = None
        self._assistant_seed = assistant_seed
        self.load_assistant(assistant_path)

        self.init_state()
        # self._current_action = self.glop_env.action_space()
        # self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)
        # self._reward = self.glop_env.reward_range[0]
        # self._done = False
        # self._info = {}

        # to control which action will be done when
        self.next_computation = None
        self.next_computation_kwargs = {}

    def load_assistant(self, assistant_path):
        print(f"attempt to load assistant with path : \"{assistant_path}\"")
        has_been_loaded = False
        if assistant_path != "" and not assistant_path in {"unload", "\"", "\"\""}:
            # a real path has been set up
            tmp = load_assistant(assistant_path, self._assistant_seed, self.glop_env.copy())
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
            self.assistant.seed(int(self._assistant_seed))

        if has_been_loaded:
            # TODO do i "change the past" ?
            for step_id in range(len(self.past_envs)):
                _current_action, \
                _assistant_action, \
                _obs, _reward, _done, _info, \
                glop_env = self.past_envs[step_id]
                _assistant_action = self.assistant.act(_obs, _reward, _done)
                self.past_envs[step_id] = (_current_action,
                                           _assistant_action,
                                           _obs, _reward, _done, _info,
                                           glop_env)
        print("assistant loaded")
        return has_been_loaded

    def do_computation(self):
        # print(f"do_computation: {self.next_computation = }")
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
            return self.step()
        elif self.next_computation == "step_rec_fast":
            # currently not used !
            res = None
            for i in range(int(self.next_computation_kwargs["nb_step_gofast"])):
                res = self.step()
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
            raise RuntimeError(f"Unknown method to call: {self.next_computation = }")
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

    @property
    def action_space(self):
        return self.glop_env.action_space

    @property
    def observation_space(self):
        return self.glop_env.observation_space

    @property
    def obs(self):
        return self._obs

    @property
    def current_action(self):
        return self._current_action

    @property
    def sim_obs(self):
        return self._sim_obs

    @property
    def is_done(self):
        return self._done

    def take_last_action(self):
        """take the same action as last time"""
        if self.past_envs:
            self._current_action = self.past_envs[-1][0]

    def seed(self, seed):
        """seed and reset the environment"""
        seeds = self.glop_env.seed(seed)
        self.init_state()
        return seeds

    def step(self, action=None):
        if self._done:
            self.stop_computation()
            return self.obs, self._reward, self._done, self._info

        if action is None:
            action = self._current_action
        else:
            # TODO is this correct ? I never really tested that
            self._current_action = action

        # to improve deep copy speeds
        time.sleep(0.1)
        beg_ = time.time()
        # beg__ = time.time()
        saved_act = copy.deepcopy(self._current_action)
        # end__ = time.time()
        # print(f"\t\t\t time to copy the saved_act: {end__ - beg__:.3f}s")
        # beg__ = time.time()
        saved_assistant_act = copy.deepcopy(self._assistant_action)
        # end__ = time.time()
        # print(f"\t\t\t time to copy the saved_assistant_act: {end__ - beg__:.3f}s")
        # beg__ = time.time()
        obs_cpy = self._obs.copy()
        # end__ = time.time()
        # print(f"\t\t\t time to copy the obs: {end__ - beg__:.3f}s")
        # beg__ = time.time()
        env_cpy = self.glop_env.copy()
        # end__ = time.time()
        # print(f"\t\t\t time to copy the glop_env: {end__ - beg__:.3f}s")
        this_state = (saved_act,
                      saved_assistant_act,
                      obs_cpy, self._reward, self._done, self._info,
                      env_cpy)
        end_ = time.time()
        # print(f"\t\t time to copy the state: {end_-beg_:.3f}s")

        self.past_envs.append(this_state)
        self._assistant_action = None
        self._obs, self._reward, self._done, self._info = self.glop_env.step(action)
        if self._obs.time_since_last_alarm == 0:
            print("The assistant raised an alarm !")
            self.stop_computation()
        self._fill_info_vect()
        if not self._done:
            self.choose_next_action()
            self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self._current_action)
        else:
            self._sim_done = True
            self._sim_reward = self.glop_env.reward_range[0]
            self._sim_info = {}
            self._sim_obs.set_game_over(self.glop_env)
        # print(f"grid2game env.py: {self._obs.current_step} / {self._obs.max_step}")
        return self.obs, self._reward, self._done, self._info

    def choose_next_action(self):
        self._assistant_action = None
        if self.next_action_from == self.ASSISTANT:
            # self._assistant_action = self.glop_env.action_space.sample()
            self._assistant_action = self.assistant.act(self._obs, self._reward, self._done)
            self._current_action = copy.deepcopy(self._assistant_action)
        elif self.next_action_from == self.LIKE_PREVIOUS:
            # next action should be like the previous one
            pass
        elif self.next_action_from == self.DO_NOTHING:
            self._current_action = self.glop_env.action_space()
        else:
            raise RuntimeError("Unsupported next action")

    def simulate(self, action=None):
        if action is None:
            action = self._current_action
        self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(action)
        return self._sim_obs, self._sim_obs, self._sim_reward, self._sim_done, self._sim_info

    def back(self):
        if len(self.past_envs):
            is_this_done = self._done
            self.glop_env.close()
            *self.past_envs, (self._current_action,
                              self._assistant_action,
                              self._obs, self._reward, self._done, self._info,
                              self.glop_env) = self.past_envs
            self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)
            if not is_this_done:
                self._pop_vects()

    def reset(self):
        for *_, glop_env in self.past_envs:
            glop_env.close()
        self.init_state()

    def init_state(self):
        self.past_envs = []
        self._obs = self.glop_env.reset()
        if self.assistant is not None:
            self.assistant.reset(self._obs)
        self._current_action = self.glop_env.action_space()
        self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)
        self._reward = self.glop_env.reward_range[0]
        self._done = False
        self._info = {}

        self._sum_load = []
        self._max_line_flow = []
        self._secondmax_line_flow = []
        self._thirdmax_line_flow = []
        self._sum_solar = []
        self._sum_wind = []
        self._sum_thermal = []
        self._sum_hydro = []
        self._sum_nuclear = []
        self._datetimes = []

        self._fill_info_vect()

    def _fill_info_vect(self):
        if self._done:
            # don't had data corresponding to the last observation, which is "wrong"
            return
        self._sum_load.append(np.sum(self._obs.load_p))
        rhos_ = np.partition(self._obs.rho.flatten(), -3)
        self._max_line_flow.append(rhos_[-1])
        self._secondmax_line_flow.append(rhos_[-2])
        self._thirdmax_line_flow.append(rhos_[-3])
        if hasattr(self._obs, "gen_p"):
            vect_ = self._obs.gen_p
        else:
            vect_ = self._obs.prod_p
            import warnings
            warnings.warn("DEPRECATED: please use grid2op >= 1.5 for benefiting from all grid2game feature",
                          DeprecationWarning)
        self._sum_solar.append(np.sum(vect_[self.glop_env.gen_type == "solar"]))
        self._sum_wind.append(np.sum(vect_[self.glop_env.gen_type == "wind"]))
        self._sum_thermal.append(np.sum(vect_[self.glop_env.gen_type == "thermal"]))
        self._sum_hydro.append(np.sum(vect_[self.glop_env.gen_type == "hydro"]))
        self._sum_nuclear.append(np.sum(vect_[self.glop_env.gen_type == "nuclear"]))
        self._datetimes.append(self._obs.get_time_stamp())

    def _pop_vects(self):
        *self._sum_load, _ = self._sum_load
        *self._max_line_flow, _ = self._max_line_flow
        *self._secondmax_line_flow, _ = self._secondmax_line_flow
        *self._thirdmax_line_flow, _ = self._thirdmax_line_flow
        *self._sum_solar, _ = self._sum_solar
        *self._sum_wind, _ = self._sum_wind
        *self._sum_thermal, _ = self._sum_thermal
        *self._sum_hydro, _ = self._sum_hydro
        *self._sum_nuclear, _ = self._sum_nuclear
        *self._datetimes, _ = self._datetimes

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
        if self.past_envs:
            self._current_action = copy.deepcopy(self.past_envs[-1][0])
        else:
            self.next_action_is_dn()

    def next_action_is_assistant(self):
        """the next action is chosen to be given by the assistant"""
        if self.next_action_from == self.ASSISTANT:
            return

        self.next_action_from = self.ASSISTANT
        if self._assistant_action is None:
            # self._assistant_action = self.glop_env.action_space.sample()
            self._assistant_action = self.assistant.act(self._obs, self._reward, self._done)
        self._current_action = copy.deepcopy(self._assistant_action)

