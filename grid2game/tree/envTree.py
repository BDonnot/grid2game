# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import copy
from typing import Union
import numpy as np
import plotly
import plotly.graph_objects as go

from grid2op.Action import BaseAction
from grid2op.Observation import BaseObservation
from grid2op.Agent import BaseAgent
from grid2op.Environment import BaseEnv

from grid2game.tree.node import Node


class EnvTree(object):
    """
    Store the whole studied environment as a tree

    And also implements the possibility to plot it.
    """
    def __init__(self):
        self._all_nodes = []
        self._current_node = None

    def root(self,
             assistant: Union[BaseAgent, None],
             env: BaseEnv,
             obs: BaseObservation):
        """build the root of the tree"""
        node = Node(id_=0, father=None,
                    assistant=assistant, glop_env=env, obs=obs,
                    reward=None, done=False, info=None)
        self._all_nodes.append(node)
        self._current_node = node

    def make_step(self,
                  assistant: Union[BaseAgent, None],  # TODO have a member with this
                  chosen_action: BaseAction):
        """make a "step" in the tree with the given action"""
        res = self._current_node.son_for_this_action(chosen_action)
        if res is not None:
            # I "already" made this action "in the past"
            # so i retrieve what i did
            self._current_node = res.son
        else:
            # first time i do this action, so i store everything
            current_env = self._current_node._glop_env.copy()
            _obs, _reward, _done, _info = current_env.step(chosen_action)
            node = Node(assistant=assistant,
                        obs=_obs, reward=_reward, done=_done, info=_info,
                        glop_env=current_env,
                        id_=len(self._all_nodes),
                        father=self._current_node)

            # TODO check if node exist ! (not using id !)
            self._current_node.add_son(chosen_action, node)
            self._current_node = node
            self._all_nodes.append(node)

    def go_to_node(self, node: Node):
        """set the current node of the tree to be this node"""
        # TODO check that the node exist ! (using the id)
        self._current_node = node

    def plot_plotly(self) -> plotly.graph_objects.Figure:
        # see https://plotly.com/python/tree-plots/
        Xn = [node.step for node in self._all_nodes]
        Yn = [0.]
        nb_ts = max(Xn)
        encounter = np.zeros(nb_ts + 1)
        for node in self._all_nodes[1:]:
            # for all non root node: assign the position in the Y axis,
            # that depends on the number of bother
            nb_siblings = len(node.father._act_to_sons)
            pos_y = Yn[node.father.id]
            if nb_siblings > 1:
                # TODO this should changed based on the number of children of my siblings too !
                pos_y += (-1)**encounter[node.step] * (encounter[node.step] // 2 + 1)

            encounter[node.step] += 1
            Yn.append(pos_y)

        Xe = []
        Ye = []
        texts = []
        for node in self._all_nodes:
            # run through all the node and connect it to its children, if any
            my_x = Xn[node.id]
            my_y = Yn[node.id]
            for link in node.get_actions_to_son():
                if link.son is not None:
                    # This link has a son
                    tmp_x = Xn[link.son.id]
                    tmp_y = Yn[link.son.id]
                    Xe += [my_x, tmp_x, None]
                    Ye += [my_y, tmp_y, None]
                    texts.append(f"{link.action}")

        fig = go.Figure()
        # plot the edges / link / actions
        fig.add_trace(go.Scatter(x=Xe,
                                 y=Ye,
                                 mode='lines',
                                 line=dict(color='rgb(210,210,210)', width=1),
                                 hoverinfo='text',
                                 text=texts,
                                 ))

        # plot the vertices / node / observations
        fig.add_trace(go.Scatter(x=Xn,
                                 y=Yn,
                                 mode='markers',
                                 name='bla',
                                 marker=dict(symbol='circle-dot',
                                             size=18,
                                             color='#6175c1',    #'#DB4551',
                                             line=dict(color='rgb(50,50,50)', width=1)
                                             ),
                                 text=[node.id for node in self._all_nodes],
                                 hoverinfo='text',
                                 opacity=0.8
                                 ))
        return fig


if __name__ == "__main__":
    import grid2op
    from lightsim2grid import LightSimBackend
    import pdb
    env = grid2op.make("l2rpn_case14_sandbox", backend=LightSimBackend())
    obs = env.reset()
    assistant = None

    tree = EnvTree()
    tree.root(assistant=assistant, obs=obs, env=env)
    assert len(tree._all_nodes) == 1
    assert tree._current_node.step == 0

    act = env.action_space()
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 2
    assert tree._current_node.step == 1

    tree.go_to_node(tree._all_nodes[0])
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 2
    assert tree._current_node.step == 1

    tree.go_to_node(tree._all_nodes[0])
    act = env.action_space({"set_line_status": [(0, -1)]})
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 3
    assert tree._current_node.step == 1

    tree.go_to_node(tree._all_nodes[0])
    act = env.action_space({"set_line_status": [(1, -1)]})
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 4
    assert tree._current_node.step == 1

    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 5
    assert tree._current_node.step == 2

    fig = tree.plot_plotly()
    fig.show()




