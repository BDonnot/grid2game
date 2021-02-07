# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import grid2op


class Env(object):
    def __init__(self, env_name, **kwargs):
        self.glop_env = grid2op.make(env_name, **kwargs)
        self._obs = self.glop_env.reset()
        self.past_envs = []
        self._current_action = self.glop_env.action_space()
        self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(self.current_action)

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

    def seed(self, seed):
        return self.glop_env.seed(seed)

    def step(self, action=None):
        if action is None:
            action = self._current_action
        self.past_envs.append(self.glop_env.copy())
        self._obs, reward, done, info = self.glop_env.step(action)
        return self.obs, reward, done, info

    def simulate(self, action=None):
        if action is None:
            action = self._current_action
        self._sim_obs, self._sim_obs, self._sim_reward, self._sim_done, self._sim_info = self._obs.simulate(action)
        return self._sim_obs, self._sim_obs, self._sim_reward, self._sim_done, self._sim_info
