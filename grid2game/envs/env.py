# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.
import warnings
import numpy as np

import grid2op
from grid2op.Action import PlayableAction
from grid2op.Backend import PandaPowerBackend

try:
    from lightsim2grid import LightSimBackend
    bkClass = LightSimBackend
except ImportError:
    bkClass = PandaPowerBackend


class Env(object):
    def __init__(self, env_name, **kwargs):
        # TODO some configuration here
        self.glop_env = grid2op.make(env_name,
                                     **kwargs,
                                     backend=bkClass(),
                                     action_class=PlayableAction)

        # define variables
        self._obs = None
        self.past_envs = None
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

        self.init_state()
        # self._current_action = self.glop_env.action_space()
        # self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)
        # self._reward = self.glop_env.reward_range[0]
        # self._done = False
        # self._info = {}

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
        if action is None:
            action = self._current_action
        self.past_envs.append((self._current_action,
                               self._obs.copy(), self._reward, self._done, self._info,
                               self.glop_env.copy()))
        self._obs, self._reward, self._done, self._info = self.glop_env.step(action)
        self.fill_info_vect()
        self._current_action = self.glop_env.action_space()
        if not self._done:
            self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(action)
        else:
            self._sim_done = True
            self._sim_reward = self.glop_env.reward_range[0]
            self._sim_info = {}
            self._sim_obs.set_game_over()
        return self.obs, self._reward, self._done, self._info

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
                              self._obs, self._reward, self._done, self._info,
                              self.glop_env) = self.past_envs
            self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)
            if not is_this_done:
                self.pop_vects()

    def reset(self):
        for *_, glop_env in self.past_envs:
            glop_env.close()
        self.init_state()

    def init_state(self):
        self.past_envs = []
        self._obs = self.glop_env.reset()
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

        self.fill_info_vect()

    def fill_info_vect(self):
        if self._done:
            # don't had data corresponding to the last observation, which is "wrong"
            return
        self._sum_load.append(np.sum(self._obs.load_p))
        rhos_ = np.partition(self._obs.rho.flatten(), -3)
        self._max_line_flow.append(rhos_[-1])
        self._secondmax_line_flow.append(rhos_[-2])
        self._thirdmax_line_flow.append(rhos_[-3])
        self._sum_solar.append(np.sum(self._obs.gen_p[self.glop_env.gen_type == "solar"]))
        self._sum_wind.append(np.sum(self._obs.gen_p[self.glop_env.gen_type == "wind"]))
        self._sum_thermal.append(np.sum(self._obs.gen_p[self.glop_env.gen_type == "thermal"]))
        self._sum_hydro.append(np.sum(self._obs.gen_p[self.glop_env.gen_type == "hydro"]))
        self._sum_nuclear.append(np.sum(self._obs.gen_p[self.glop_env.gen_type == "nuclear"]))
        self._datetimes.append(self._obs.get_time_stamp())

    def pop_vects(self):
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
