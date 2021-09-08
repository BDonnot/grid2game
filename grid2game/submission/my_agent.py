# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import numpy as np
from grid2op.dtypes import dt_float
from grid2op.Agent import GreedyAgent


class MyAgent(GreedyAgent):
    """
    This is a heuristic agent that performs relatively well in the l2rpn_case14_sandbox, mainly because
    this environment allows to switch on / off powerline constantly without any "cooldown".

    Only works correctly for "l2rpn_case14_sandbox" at the moment !
    """

    def __init__(self, action_space):
        GreedyAgent.__init__(self, action_space)
        self.tested_action_curtail = None
        self.tested_action_redisp = None
        self.tested_action_lines = None
        self.use_reward = False
        self.alpha_redisp = 0.0003  # to limit the total amount of redispatching
        self.alpha_overflow = 1.  # to limit the total amount of redispatching
        self.exponent_cap = 2

    def get_score_to_aim(self, sim_obs):
        cap = np.maximum((1 - sim_obs.rho), 0.)
        cap = cap ** self.exponent_cap
        cap = np.mean(cap)
        redisp = np.sum(np.abs(sim_obs.actual_dispatch))
        nb_powerline_overflow = np.sum(sim_obs.rho > 1.)
        return cap - self.alpha_redisp * redisp - self.alpha_overflow * nb_powerline_overflow

    def act(self, observation, reward, done=False):
        """
        By definition, all "greedy" agents are acting the same way. The only thing that can differentiate multiple
        agents is the actions that are tested.

        These actions are defined in the method :func:`._get_tested_action`. This :func:`.act` method implements the
        greedy logic: take the actions that maximizes the instantaneous reward on the simulated action.

        Parameters
        ----------
        observation: :class:`grid2op.Observation.Observation`
            The current observation of the :class:`grid2op.Environment.Environment`

        reward: ``float``
            The current reward. This is the reward obtained by the previous action

        done: ``bool``
            Whether the episode has ended or not. Used to maintain gym compatibility

        Returns
        -------
        res: :class:`grid2op.Action.Action`
            The action chosen by the bot / controller / agent.

        """
        self.tested_action = self._get_tested_action(observation)
        if len(self.tested_action) > 1:
            self.resulting_rewards = np.full(shape=len(self.tested_action), fill_value=np.NaN, dtype=dt_float)
            sim_obs_saved = []
            for i, action in enumerate(self.tested_action):
                simul_obs, simul_reward, simul_has_error, simul_info = observation.simulate(action)
                if not self.use_reward:
                    simul_reward = self.get_score_to_aim(simul_obs)
                    sim_obs_saved.append(simul_obs)
                self.resulting_rewards[i] = simul_reward
            reward_idx = int(np.argmax(self.resulting_rewards))  # rewards.index(max(rewards))
            best_action = self.tested_action[reward_idx]
        else:
            best_action = self.tested_action[0]
        return best_action

    def _get_tested_action(self, observation):
        if self.tested_action_curtail is None:
            res = self.get_all_unitary_curtail(num_bin=5, min_value=0.8)
            self.tested_action_curtail = res
        if self.tested_action_redisp is None:
            res = self.action_space.get_all_unitary_redispatch(self.action_space, num_down=2, num_up=2)
            self.tested_action_redisp = res
        if self.tested_action_lines is None:
            self.tested_action_lines = [self.action_space({"set_line_status": [(14, -1)]}),
                                        self.action_space({"set_line_status": [(14, +1)]}),
                                        ]
        res = [self.action_space({})]  # add the do nothing

        # for speed i consider i try redispatching only if a powerline on the grid is above 90%
        if observation.rho.max() >= 0.95 or np.sum(np.abs(observation.actual_dispatch)) > 5:

            # even in grid2op i need to keep some sort of "primary / secondary reserve", in this case 15MW
            # and i also ensure that i have 20 MW available on gen 0 and 10 on gen 1 (for increase of load)
            gen_ratio = observation.gen_pmax[observation.gen_redispatchable]
            gen_ratio -= observation.gen_p[observation.gen_redispatchable]
            gen_ratio = np.sum(np.maximum(gen_ratio, 0.))
            if gen_ratio >= 20 and observation.gen_p[0] <= 120 and observation.gen_p[1] <= 115:
                res += self.tested_action_curtail
                res += self.tested_action_redisp

            if observation.rho.max() >= 0.95:
                # i add the line actions just in case of emergency
                res += self.tested_action_lines

        # I attempt to reconnect powerline if can reconnect some
        line_stat_s = observation.line_status
        cooldown = observation.time_before_cooldown_line
        return res

    def get_all_unitary_curtail(self, num_bin=10, min_value=0.5):
        action_space = self.action_space
        res = []
        n_gen = len(action_space.gen_renewable)

        for gen_idx in range(n_gen):
            # Skip non-renewable generators (they cannot be curtail)
            if not action_space.gen_renewable[gen_idx]:
                continue
            # Create evenly spaced interval
            ramps = np.linspace(min_value, 1.0, num=num_bin)

            # Create ramp up actions
            for ramp in ramps:
                action = action_space({"curtail": [(gen_idx, ramp)]})
                res.append(action)
        return res

    def get_all_unitary_redispatch(self, obs, num_up=2, num_down=2):
        action_space = self.action_space
        res = []
        n_gen = len(action_space.gen_redispatchable)
        action_space = self.action_space
        for gen_idx in range(n_gen):
            # Skip non-dispatchable generators
            if not action_space.gen_redispatchable[gen_idx]:
                continue

            with_up = False
            # Create evenly spaced positive interval
            if obs.gen_p[gen_idx] > obs.gen_pmax[gen_idx] - 5. * obs.gen_max_ramp_up[gen_idx]:
                ramps_up = np.linspace(0.0, action_space.gen_max_ramp_up[gen_idx], num=num_up)
                ramps_up = ramps_up[1:]  # Exclude redispatch of 0MW
                with_up = True

            # Create evenly spaced negative interval
            ramps_down = np.linspace(-action_space.gen_max_ramp_down[gen_idx], 0.0, num=num_down)
            ramps_down = ramps_down[:-1]  # Exclude redispatch of 0MW

            # Merge intervals
            if with_up:
                ramps = np.append(ramps_up, ramps_down)
            else:
                ramps = ramps_down

            # Create ramp up actions
            for ramp in ramps:
                action = action_space({"redispatch": [(gen_idx, ramp)]})
                res.append(action)
        return res
