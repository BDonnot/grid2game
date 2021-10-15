# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import copy
import re
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
        self._last_action = None
        self.__is_init = False
        self.fig_timeline = None

    def root(self,
             assistant: Union[BaseAgent, None],
             env: BaseEnv,
             obs: BaseObservation):
        """build the root of the tree"""
        node = Node(id_=0, father=None,
                    assistant=assistant,
                    glop_env=env.copy(),
                    obs=obs,
                    reward=None, done=False, info=None)
        self._all_nodes.append(node)
        self._current_node = node
        self.__is_init = True
        self.init_plot_timeline()

    def init_plot_timeline(self) -> None:
        """initialize the plot for the timeline"""
        self.fig_timeline = go.Figure()

        # plot the edges / link / actions
        color_links = 'rgb(210,210,210)'
        col_background = 'rgba(229, 236, 246, 0.1)'
        col_realtime = 'rgba(255, 140, 0, 1)'

        # the edges / links / action
        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='lines',
                                               name="edges",
                                               line=dict(color=color_links, width=1),
                                               hoverinfo='none',
                                               text=[],
                                               ))

        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='markers',
                                               name='edges_center',
                                               marker=dict(symbol='circle-dot',
                                                           size=5,
                                                           color='#6175c1',
                                                           line=dict(color=color_links, width=1)
                                                           ),
                                               text=[""],
                                               hoverinfo='text',
                                               opacity=0.8
                                               ))

        # plot the vertices / node / observations
        # regular vertices
        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='markers',
                                               name='nodes',
                                               marker=dict(symbol='circle-dot',
                                                           size=9,
                                                           color='#6175c1',    #'#DB4551',
                                                           line=dict(color='rgb(50,50,50)', width=3)
                                                           ),
                                               text=[],
                                               hoverinfo='text',
                                               opacity=0.8
                                               ))
        # game over vertices
        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='markers',
                                               name='nodes_game_over',
                                               marker=dict(symbol='x',
                                                           size=15,
                                                           color='crimson'
                                                           ),
                                               text=[],
                                               hoverinfo='text',
                                               opacity=0.8
                                               ))

        # game over vertices
        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='markers',
                                               name='nodes_success',
                                               marker=dict(symbol='star',
                                                           size=15,
                                                           color='darkgreen'
                                                           ),
                                               text=[],
                                               hoverinfo='text',
                                               opacity=0.8
                                               ))
        # real time vertical bar
        self.fig_timeline.add_trace(go.Scatter(x=[0, 0],
                                               y=[-10, 10],
                                               mode='lines',
                                               name="real_time",
                                               line=dict(color=col_realtime, dash="dot"),
                                               hoverinfo='none',
                                               text=[],
                                               ))

        self.fig_timeline.update_xaxes(range=[-0.1, self._current_node.obs.max_step], showgrid=False, visible=False)
        self.fig_timeline.update_yaxes(range=[-2, 2], showgrid=False, visible=False)
        # vertical line to show current step
        self.fig_timeline.update_layout({"plot_bgcolor": col_background,
                                         "paper_bgcolor": col_background,
                                         # "title": "Timeline"
                                        })
        self.fig_timeline.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                        # height=int(50),
                                        showlegend=False)

    def make_step(self,
                  assistant: Union[BaseAgent, None],  # TODO have a member with this
                  chosen_action: BaseAction):
        """make a "step" in the tree with the given action"""
        if not self.__is_init:
            raise RuntimeError("You are trying to use a non initialized envTree.")

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

    def layout_igraph(self):
        """bad layout, not really working"""
        import igraph
        graph = igraph.Graph()
        # add the node
        graph.add_vertices(len(self._all_nodes))

        # add the edges
        for node in self._all_nodes:
            for link in node.get_actions_to_sons():
                if link.son is not None:
                    graph.add_edge(node.id, link.son.id)
        lay = graph.layout('rt')

        # position of nodes
        Xn = [lay[i][1] for i in range(len(self._all_nodes))]
        Yn = [lay[i][0] for i in range(len(self._all_nodes))]

        # position of edges
        Xe = []
        Ye = []
        # center of edges
        Xe_c = []
        Ye_c = []
        for node in self._all_nodes:
            for link in node.get_actions_to_sons():
                if link.son is not None:
                    Xe += [Xn[node.id], Xn[link.son.id], None]
                    Ye += [Yn[node.id], Yn[link.son.id], None]
                    Xe_c.append(0.5 * (Xn[node.id] + Xn[link.son.id]))
                    Ye_c.append(0.5 * (Yn[node.id] + Yn[link.son.id]))

        # add the text on the action / link / edges
        texts = []
        for node in self._all_nodes:
            # run through all the node and connect it to its children, if any
            for link in node.get_actions_to_sons():
                    txt = ""
                    if link.action.can_affect_something():
                        txt = re.sub("\n", "<br>", link.action.__str__())
                    texts.append(txt)
        return Xn, Yn, Xe, Ye, Xe_c, Ye_c, texts

    def layout_manual(self):
        """
        this layout make sure nothing can be aligned if it does not come from the same root

        For now, its main drawback is that it always add nodes "on top" of the others, instead of trying to center
        them.
        """
        Xn = [node.step for node in self._all_nodes]
        Yn = [0.]

        # compute the maximum width of the stuff
        width = [0 for _ in self._all_nodes]
        for node in self._all_nodes[::-1]:
            if len(node.get_actions_to_sons()) == 0:
                width[node.id] = 1
            for link in node.get_actions_to_sons():
                # this is not a terminal node, the width is defined as the sum(width_children)
                width[node.id] += width[link.son.id]

        son_id = np.zeros(len(Xn))
        for node in self._all_nodes[1:]:
            # for all non root node: assign the position in the Y axis,
            # that depends on the number of bother
            pos_y = Yn[node.father.id]
            # if node.id >= 1:
            #     pdb.set_trace()
            if width[node.father.id] != width[node.id]:
                pos_y += son_id[node.father.id]
                son_id[node.father.id] += width[node.id]
            Yn.append(pos_y)

        Xe = []
        Ye = []
        texts = []
        Xe_c = []
        Ye_c = []
        for node in self._all_nodes:
            # run through all the node and connect it to its children, if any
            my_x = Xn[node.id]
            my_y = Yn[node.id]
            for link in node.get_actions_to_sons():
                if link.son is not None:
                    # This link has a son
                    tmp_x = Xn[link.son.id]
                    tmp_y = Yn[link.son.id]
                    Xe += [my_x, tmp_x, None]
                    Ye += [my_y, tmp_y, None]
                    Xe_c.append(0.5 * (my_x + tmp_x))
                    Ye_c.append(0.5 * (my_y + tmp_y))
                    txt = "do nothing"
                    if link.action.can_affect_something():
                        txt = re.sub("\n", "<br>", link.action.__str__())
                    texts.append(txt)
        return np.array(Xn), np.array(Yn), Xe, Ye, Xe_c, Ye_c, texts

    def plot_plotly(self) -> plotly.graph_objects.Figure:
        # see https://plotly.com/python/tree-plots/

        # retrieve the layout
        Xn, Yn, Xe, Ye, Xe_c, Ye_c, texts = self.layout_manual()

        # now filter them based on game over or not
        node_normal = []
        node_game_over = []
        node_sucess = []
        for node in self._all_nodes:
            if node.done:
                if node.step != self._current_node.obs.max_step:
                    node_game_over.append(node.id)
                else:
                    node_sucess.append(node.id)
            else:
                node_normal.append(node.id)

        # and now plot the figure
        self.fig_timeline.update_traces(x=Xn[node_normal],
                                        y=Yn[node_normal],
                                        text=[f"{id_}" for id_ in node_normal],
                                        selector=dict(name="nodes"))
        self.fig_timeline.update_traces(x=Xn[node_game_over],
                                        y=Yn[node_game_over],
                                        text=[f"{id_}" for id_ in node_game_over],
                                        selector=dict(name="nodes_game_over"))
        self.fig_timeline.update_traces(x=Xn[node_sucess],
                                        y=Yn[node_sucess],
                                        text=[f"{id_}" for id_ in node_sucess],
                                        selector=dict(name="nodes_success"))
        self.fig_timeline.update_traces(x=Xe,
                                        y=Ye,
                                        selector=dict(name="edges"))
        self.fig_timeline.update_traces(x=Xe_c,
                                        y=Ye_c,
                                        text=texts,
                                        selector=dict(name="edges_center"))
        self.fig_timeline.update_traces(x=[self.current_node.step, self.current_node.step],
                                        selector=dict(name="real_time"))

        return self.fig_timeline

    def clear(self) -> None:
        """clear all the data stored in the tree"""
        for node in self._all_nodes:
            node.clear()
        del self._all_nodes
        self._all_nodes = []
        self._current_node = None
        self.__is_init = False

    @property
    def current_node(self) -> "Node":
        """retrieve the current node, which is displayed by the UI"""
        return self._current_node

    def get_last_action(self) -> BaseAction:
        """retrieve the last action performed on the grid"""
        res = self._current_node._glop_env.action_space()
        if self._current_node.id == 0:
            # it's the root of the tree, last action does not exist, but i say it's do nothing
            res = self._current_node._glop_env.action_space()
        else:
            father = self._current_node.father
            for link in father.get_actions_to_sons():
                if link.son.id == self.current_node.id:
                    res = copy.deepcopy(link.action)
        return res

    def back_one_step(self) -> None:
        """back but only for one step"""
        father = self._current_node.father
        self.go_to_node(father)


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

    act = env.action_space()
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 5
    assert tree._current_node.step == 2

    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 6
    assert tree._current_node.step == 3

    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 7
    assert tree._current_node.step == 4

    tree.go_to_node(tree._all_nodes[5])
    act = env.action_space({"set_line_status": [(1, -1)]})
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 8
    assert tree._current_node.step == 4

    tree.go_to_node(tree._all_nodes[0])
    act = env.action_space({"set_line_status": [(2, -1)]})
    tree.make_step(assistant=assistant, chosen_action=act)
    assert len(tree._all_nodes) == 9
    assert tree._current_node.step == 1

    fig = tree.plot_plotly()
    fig.show()




