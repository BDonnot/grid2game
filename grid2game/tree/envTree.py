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

        self.Xn = None
        self.Yn = None

        self.margin_for_plot = 0.5

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
        self.Xn = np.array([0])
        self.Yn = np.array([0])

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

        #  success vertices
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

        # alert vertices
        self.fig_timeline.add_trace(go.Scatter(x=[],
                                               y=[],
                                               mode='markers',
                                               name='nodes_alert',
                                               marker=dict(symbol='triangle-down-dot',
                                                           size=16,
                                                           color='darkorange'
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

        self.fig_timeline.update_xaxes(range=[-self.margin_for_plot,
                                              self._current_node.obs.max_step + self.margin_for_plot],
                                       showgrid=False, visible=False)
        self.fig_timeline.update_yaxes(range=[-self.margin_for_plot, 2], showgrid=False, visible=False)
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

        chosen_action = copy.deepcopy(chosen_action)
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

            # recompute the position of the node
            # TODO optimize here to compute only the last position, and not recompute all previous positions each time !
            self.Xn, self.Yn = self.layout_manual()

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
        return np.array(Xn), np.array(Yn)

    def node_info(self):
        """computes which type of information should be displayed on which node in the timeline"""
        Xe = []
        Ye = []
        texts = []
        Xe_c = []
        Ye_c = []
        for node in self._all_nodes:
            # run through all the node and connect it to its children, if any
            my_x = self.Xn[node.id]
            my_y = self.Yn[node.id]
            for link in node.get_actions_to_sons():
                if link.son is not None:
                    # This link has a son
                    tmp_x = self.Xn[link.son.id]
                    tmp_y = self.Yn[link.son.id]
                    Xe += [my_x, tmp_x, None]
                    Ye += [my_y, tmp_y, None]
                    Xe_c.append(0.5 * (my_x + tmp_x))
                    Ye_c.append(0.5 * (my_y + tmp_y))
                    txt = "∅"
                    if link.action.can_affect_something():
                        txt = re.sub("\n", "<br>", link.action.__str__())
                    texts.append(txt)
        return Xe, Ye, Xe_c, Ye_c, texts

    def plot_plotly(self) -> plotly.graph_objects.Figure:
        # see https://plotly.com/python/tree-plots/

        # retrieve the layout
        Xe, Ye, Xe_c, Ye_c, texts = self.node_info()

        # now filter them based on game over or not
        node_normal = []
        node_game_over = []
        node_sucess = []
        node_alert = []
        for node in self._all_nodes:
            if node.done:
                if node.step != self._current_node.obs.max_step:
                    node_game_over.append(node.id)
                else:
                    node_sucess.append(node.id)
            elif np.any(node.obs.time_since_last_alarm == 0):
                node_alert.append(node.id)
            else:
                node_normal.append(node.id)

        # and now plot the figure
        self.fig_timeline.update_traces(x=self.Xn[node_normal],
                                        y=self.Yn[node_normal],
                                        text=[f"{id_}" for id_ in node_normal],
                                        selector=dict(name="nodes"))
        self.fig_timeline.update_traces(x=self.Xn[node_game_over],
                                        y=self.Yn[node_game_over],
                                        text=[f"{id_}" for id_ in node_game_over],
                                        selector=dict(name="nodes_game_over"))
        self.fig_timeline.update_traces(x=self.Xn[node_sucess],
                                        y=self.Yn[node_sucess],
                                        text=[f"{id_}" for id_ in node_sucess],
                                        selector=dict(name="nodes_success"))
        self.fig_timeline.update_traces(x=self.Xn[node_alert],
                                        y=self.Yn[node_alert],
                                        text=[f"{id_}" for id_ in node_alert],
                                        selector=dict(name="nodes_alert"))
        self.fig_timeline.update_traces(x=Xe,
                                        y=Ye,
                                        selector=dict(name="edges"))
        self.fig_timeline.update_traces(x=Xe_c,
                                        y=Ye_c,
                                        text=texts,
                                        selector=dict(name="edges_center"))
        self.fig_timeline.update_traces(x=[self.current_node.step, self.current_node.step],
                                        selector=dict(name="real_time"))
        # self.fig_timeline.update_xaxes(range=[-0.1, np.max(Xn) + 0.1], showgrid=False, visible=False)
        self.fig_timeline.update_yaxes(range=[-self.margin_for_plot, np.max(self.Yn) + self.margin_for_plot])
        return self.fig_timeline

    def clear(self) -> None:
        """clear all the data stored in the tree"""
        for node in self._all_nodes:
            node.clear()
        del self._all_nodes
        self._all_nodes = []
        self._current_node = None
        self.Xn = None
        self.Yn = None
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

    @property
    def temporal_data(self):
        return self._current_node.temporal_data

    def move_from_click(self, time_line_graph_clcked) -> int:
        """move the time from a click on the timeline"""

        if 'points' not in time_line_graph_clcked:
            # nothing has been clicked on
            return 0
        if not len(time_line_graph_clcked['points']):
            # not point have been selected
            return 0

        pts = time_line_graph_clcked['points'][0]
        if 'curveNumber' not in pts:
            # I cannot extract which curve I cliked on
            return 0

        if "pointIndex" not in pts:
            # I cannot extract the point number
            return 0

        # It does not work because of the "end" part, see https://github.com/BDonnot/grid2game/issues/17
        # if pts["curveNumber"] != 2:
        #     # I did not click a node on the graph, but something else
        #     return 0

        # retrieve the point I clicked on
        # and make sure it's the right coordinates
        posx = pts["x"]
        posy = pts["y"]
        for pt_index, node in enumerate(self._all_nodes):
            th_x = self.Xn[pt_index]
            th_y = self.Yn[pt_index]
            if th_x == posx and th_y == posy:
                # It's the right coordinates, i move there
                self.go_to_node(node)
        return 1

    def get_current_action_list(self):
        """return the list of actions from the current point in the tree up to the root"""
        res = []
        # retrieve the list of actions from me to the root
        node = self._current_node
        while True:
            if node.father is None:
                # I arrived at the root of the tree
                break
            father = node.father
            link_from_father_to_node = father.get_actions_to_sons()[node.father_id]
            res.append(link_from_father_to_node.action)
            node = father
        # I return the list, but going from root to end, and not the opposite
        return res[::-1]


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
