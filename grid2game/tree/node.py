# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

from typing import Union, List, Tuple

from grid2op.Action import BaseAction
from grid2op.Observation import BaseObservation
from grid2op.Agent import BaseAgent
from grid2op.Environment import BaseEnv

from grid2game.tree.link import Link
from grid2game.tree.temporalNodeData import TemporalNodeData


class Node(object):
    """a node represents the state of the grid at a given time"""
    def __init__(self,
                 id_: int,  # unique node identifier
                 father: Union["Node", None],
                 obs: BaseObservation,
                 glop_env: BaseEnv,
                 assistant: Union[BaseAgent, None],
                 reward: Union[float, None],
                 done: Union[bool, None],
                 info: Union[dict, None]):
        self._id: int = id_
        self._father: Union["Node", None] = father
        self.step: int = obs.current_step  # unique identifier of the node ID

        # current state of the grid
        self._obs: BaseObservation = obs
        self._reward: Union[float, None] = reward
        self._done: Union[bool, None] = done
        self._info: Union[dict, None]= info
        self._glop_env: BaseEnv = glop_env
        self._assistant_action: Union[BaseAction, None] = None
        self.fill_assistant(assistant)

        # links to my "sons"
        self._act_to_sons: List[Link] = []

        self._temporal_data = TemporalNodeData(current_obs=obs,
                                               father_node_data=self._father._temporal_data if self._father is not None else None)

    def fill_assistant(self, assistant: Union[BaseAgent, None]) -> None:
        """fill the action the assistant would have done in this node"""
        if assistant is not None:
            self._assistant_action = assistant.act(self._obs, self._reward, self._done)

    def son_for_this_action(self, action: BaseAction) -> Union[Link, None]:
        """retrieve the link (if it exists) corresponding to the action `action` performed at this node"""
        res = None
        for link in self._act_to_sons:
            if link.action == action:
                res = link
                break
        return res

    def add_son(self, action: BaseAction, son: "Node") -> Link:
        """add a son to this node"""
        res = Link(action=action, father=self)
        res.add_son(son=son)
        self._act_to_sons.append(res)
        return res

    def get_actions_to_sons(self) -> List[Link]:
        """return the list of all "outgoing" links to this node"""
        return self._act_to_sons

    @property
    def id(self) -> int:
        """return the id of the current node (unique)"""
        return self._id

    @property
    def father(self) -> Union[None, "Node"]:
        """return the father of the current node (can return None) if called on the root of the tree"""
        return self._father

    def clear(self) -> None:
        """clear this node"""
        self._glop_env.close()

    def get_obs_rewar_done_info(self) -> Tuple[BaseObservation, float, bool, dict]:
        return self._obs, self._reward, self._done, self._info

    @property
    def obs(self) -> BaseObservation:
        return self._obs

    @property
    def done(self) -> bool:
        return self._done

    @property
    def temporal_data(self):
        return self._temporal_data