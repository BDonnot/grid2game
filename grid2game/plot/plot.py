# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import plotly.graph_objects as go
import cmath

from grid2op.PlotGrid import PlotPlotly
from grid2op.Space import GridObjects
import plotly.colors as pc


class PlotParams(object):
    def __init__(self):
        ### bus color
        self.col_bus1 = "red"
        self.col_bus2 = "blue"
        self.col_deact = "black"

        ################ from grid2Op, for gen
        # TODO color for gen too
        self._gen_radius = 12
        self._gen_fill_color = "LightGreen"
        self._gen_line_color = "black"
        self._gen_line_width = 1
        self._gen_prefix = "b"
        self._marker_gen = dict(size=self._gen_radius,
                                color=self._gen_fill_color,
                                showscale=False,
                                line=dict(
                                    width=self._gen_line_width,
                                    color=self._gen_line_color
                                ),
                                opacity=0.7
                                )

        ################# from grid2op, for substation
        self._sub_radius = 25
        self._sub_fill_color = "PaleTurquoise"
        self._sub_line_color = "black"
        self._sub_line_width = 1
        self._marker_sub = dict(size=self._sub_radius,
                                color=self._sub_fill_color,
                                showscale=False,
                                line=dict(
                                    width=self._sub_line_width,
                                    color=self._sub_line_color
                                )
                                )

        #################### from grid2op, for lines
        self._line_prefix = "a"
        self.line_color_scheme = pc.sequential.Blues_r[:4] + \
                                 pc.sequential.Oranges[4:6] + \
                                 pc.sequential.Reds[-3: -1]
        self._line_bus_radius = 10
        self._line_bus_colors = ["black", "red", "lime"]
        self._bus_prefix = "_bus_"
        self._or_prefix = "_or_"
        self._ex_prefix = "_ex_"
        self._line_arrow_radius = 10
        self._line_arrow_len = 5
        self._arrow_prefix = "_->_"

        ################ from grid2Op, for load
        # TODO color for load too
        self._load_radius = 12
        self._load_fill_color = "DarkOrange"
        self._load_line_color = "black"
        self._load_line_width = 1
        self._load_prefix = "c"
        self._marker_load = dict(size=self._load_radius,
                                 color=self._load_fill_color,
                                 showscale=False,
                                 line=dict(
                                     width=self._load_line_width,
                                     color=self._load_line_color
                                 ),
                                 opacity=0.7
                                 )

        ################ from grid2Op, for load
        # TODO color for storage too
        self._storage_radius = 12
        self._storage_fill_color = "rosybrown"
        self._storage_line_color = "black"
        self._storage_line_width = 1
        self._storage_prefix = "s"
        self._marker_storage = dict(size=self._storage_radius,
                                    color=self._storage_fill_color,
                                    showscale=False,
                                    line=dict(
                                        width=self._storage_line_width,
                                        color=self._storage_line_color
                                    ),
                                    opacity=0.7
                                    )


class Plot(PlotParams):
    def __init__(self, observation_space):
        super().__init__()
        self.glop_plot = PlotPlotly(observation_space)
        self.grid = GridObjects.init_grid(observation_space)

        # process the layout (position of everything)
        self.layout = self.glop_plot._grid_layout
        self.ids = {nm: id_ for id_, nm in enumerate(self.grid.name_load)}
        self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_gen)})
        self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_storage)})
        self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_sub)})
        self.process_lines_layout()

        # initialize the figures
        self.figure_rt = go.Figure()
        self.figure_forecat = go.Figure()
        self.width = 1280
        self.height = 720

        # and the units
        self.line_info = "rho"
        self.line_side = "or"
        self.load_info = "p"
        self.gen_info = "p"
        self.storage_info = "p"

    def process_lines_layout(self):
        """compute pos_or and pos_ex of both the extremity of the powerline and upadte the self.ids"""
        for id_, nm in enumerate(self.grid.name_line):
            self.ids[nm] = id_

            sub_id_or = self.grid.line_or_to_subid[id_]
            sub_id_ex = self.grid.line_ex_to_subid[id_]

            nm_subor = self.grid.name_sub[sub_id_or]
            nm_subex = self.grid.name_sub[sub_id_ex]

            pos_sub_or = self.layout[nm_subor]
            pos_sub_ex = self.layout[nm_subex]

            z_subor = pos_sub_or[0] + 1j*pos_sub_or[1]
            z_subex = pos_sub_ex[0] + 1j*pos_sub_ex[1]

            diff_ = z_subex - z_subor
            r_diff, theta_diff = cmath.polar(diff_)

            zline_or = z_subor + (self._sub_radius) * cmath.exp(1j * theta_diff)
            zline_ex = z_subor + (r_diff - self._sub_radius) * cmath.exp(1j * theta_diff)
            line_or_pos = zline_or.real, zline_or.imag
            line_ex_pos = zline_ex.real, zline_ex.imag
            self.layout[nm] = (line_or_pos, line_ex_pos)

    def plot_aux(self, obs, figure):
        self.clear_figure(figure)
        figure = go.Figure()
        for nm in self.grid.name_sub:
            self._one_sub(nm, obs, figure)
        for nm in self.grid.name_load:
            self._one_load(nm, obs, figure)
        for nm in self.grid.name_gen:
            self._one_gen(nm, obs, figure)
        for nm in self.grid.name_line:
            self._one_line(nm, obs, figure)
        for nm in self.grid.name_storage:
            self._one_storage(nm, obs, figure)
        self._set_layout(figure)
        return figure

    def clear_figure(self, fig):
        fig.data = []
        fig.layout = {}

    def plot_rt(self, obs):
        """plot the real time figure"""
        self.figure_rt = self.plot_aux(obs, self.figure_rt)
        return self.figure_rt

    def plot_forecat(self, obs):
        """plot the real time observation"""
        self.figure_forecat = self.plot_aux(obs, self.figure_forecat)
        return self.figure_forecat

    def _set_layout(self, fig):
        fig.update_layout(width=self.width,
                          height=self.height,
                          xaxis=dict(visible=False),
                          yaxis=dict(visible=False),
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=0, r=0, b=0, t=0, pad=0),
                          )

    def _one_sub(self, name, obs, figure):
        """draw one substation"""
        # retrieve its id
        id_ = self.ids[name]

        # find position
        (pos_x, pos_y) = self.layout[name]

        # plot the substation itself
        figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                    mode="markers",
                                    # text=[text],
                                    name=name,
                                    marker=self._marker_sub,
                                    showlegend=False))

        # plot the topology
        # TODO

    @staticmethod
    def choose_label_pos(my_pos, sub_pos):
        """
        chose where the label will be displayed among:
            ['top left', 'top center', 'top right', 'middle left',
             'middle center', 'middle right', 'bottom left', 'bottom
             center', 'bottom right']
         """
        my_x, my_y = my_pos
        s_x, s_y = sub_pos
        res = "middle center"
        if my_x > s_x and my_y > s_y:
            res = 'top center'
        elif my_x <= s_x and my_y > s_y:
            res = 'middle left'
        elif my_x > s_x and my_y <= s_y:
            res = 'bottom center'
        elif my_x <= s_x and my_y <= s_y:
            res = 'middle right'
        return res

    def _one_load(self, name, obs, figure):
        """draw one load"""
        # retrieve its id
        id_ = self.ids[name]

        # find position
        (pos_x, pos_y) = self.layout[name]

        # find which text is displayed
        text = None
        if self.load_info == "p":
            text = f" {obs.load_p[id_]:.2f}MW"
        elif self.load_info == "v":
            text = f" {obs.load_v[id_]:.2f}kV"
        elif self.load_info == "q":
            text = f" {obs.load_q[id_]:.2f}MVAr"
        elif self.load_info == "name":
            text = name
        elif self.load_info == "none":
            pass
        # TODO handle some "diff" here based on previous time stamps
        else:
            raise RuntimeError(f"Unsupported load value: {self.load_info}")

        # color based on bus
        id_topo_vect = self.grid.load_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_bus = self._get_bus_color(this_bus)

        # plot the "arrow" to the substation
        sub_id = self.grid.load_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        arrow_ = go.layout.Annotation(dict(
                                x=pos_x,
                                y=pos_y,
                                xref="x", yref="y",
                                text="",
                                showarrow=True,
                                axref="x", ayref='y',
                                ax=pos_subx,
                                ay=pos_suby,
                                arrowhead=2,
                                arrowwidth=0.5,
                                arrowcolor=color_bus, )
        )
        figure.add_annotation(arrow_)
        # TODO (pos_subx, pos_suby)  based on bus

        # plot the load itself
        # TODO add a custom image here for example a house
        figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                    mode="markers",
                                    # text=[text],
                                    name=name,
                                    marker=self._marker_load,
                                    showlegend=False))

        # plot the value (text on the load)
        if text is not None:
            label_position = self.choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                        text=[text],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False))

    def _one_gen(self, name, obs, figure):
        """draw one generator"""
        # retrieve its id
        id_ = self.ids[name]

        # find position
        (pos_x, pos_y) = self.layout[name]

        # find which text is displayed
        if self.gen_info == "p":
            text = f" {obs.gen_p[id_]:.2f}MW"
        elif self.gen_info == "v":
            text = f" {obs.gen_v[id_]:.2f}kV"
        elif self.gen_info == "q":
            text = f" {obs.gen_q[id_]:.2f}MVAr"
        elif self.gen_info == "ramp_down":
            text = f" {-obs.gen_max_ramp_down[id_]:.2f}MW/(5mins)"
        elif self.gen_info == "ramp_up":
            text = f" {obs.gen_max_ramp_up[id_]:.2f}MW/(5mins)"
        elif self.gen_info == "target_dispatch":
            text = f" {obs.target_dispatch[id_]:.2f}MW"
        elif self.gen_info == "actual_dispatch":
            text = f" {obs.actual_dispatch[id_]:.2f}MW"
        elif self.gen_info == "type":
            text = f" {obs.gen_type[id_]}"
        elif self.gen_info == "name":
            text = name
        elif self.gen_info == "none":
            text = None
        # TODO handle some "diff" here based on previous time stamps
        else:
            raise RuntimeError(f"Unsupported gen. value: {self.load_info}")

        # color based on bus
        id_topo_vect = self.grid.gen_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_bus = self._get_bus_color(this_bus)

        # plot the "arrow" to the substation
        sub_id = self.grid.gen_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        arrow_ = go.layout.Annotation(dict(
                                x=pos_subx,
                                y=pos_suby,
                                xref="x", yref="y",
                                text="",
                                showarrow=True,
                                axref="x", ayref='y',
                                ax=pos_x,
                                ay=pos_y,
                                arrowhead=2,
                                arrowwidth=0.5,
                                arrowcolor=color_bus, )
        )
        # TODO (pos_subx, pos_suby)  based on bus
        figure.add_annotation(arrow_)

        # plot the gen itself
        # TODO add a custom image here depending on the type of the generator, wind, solar, etc.
        figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                    mode="markers",
                                    # text=[text],
                                    name=name,
                                    marker=self._marker_gen,
                                    showlegend=False))

        # plot the value (text on the gen)
        if text is not None:
            label_position = self.choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                        text=[text],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False))

    def _get_bus_color(self, this_bus):
        if this_bus == 1:
            bus_color = self.col_bus1
        elif this_bus == 2:
            bus_color = self.col_bus2
        elif this_bus == -1:
            bus_color = self.col_deact
        else:
            raise RuntimeError(f"Invalid bus id found {this_bus} (should be either -1, 1 or 2)")
        return bus_color

    def _one_storage(self, name, obs, figure):
        """draw one storage unit"""
        # retrieve its id
        id_ = self.ids[name]

        # find position
        (pos_x, pos_y) = self.layout[name]

        # find which text is displayed
        text = None
        if self.storage_info == "p":
            text = f" {obs.storage_power[id_]:.2f}MW"
        elif self.storage_info == "MWh":
            text = f" {obs.storage_charge[id_]:.2f}MWh"
        elif self.storage_info == "name":
            text = name
        elif self.storage_info == "none":
            pass
        # TODO handle some "diff" here based on previous time stamps
        else:
            raise RuntimeError(f"Unsupported storage value: {self.storage_info}")

        # color based on bus
        id_topo_vect = self.grid.storage_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_bus = self._get_bus_color(this_bus)

        # plot the "arrow" to the substation
        sub_id = self.grid.storage_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        arrow_ = go.layout.Annotation(dict(
            x=pos_x,
            y=pos_y,
            xref="x", yref="y",
            text="",
            showarrow=True,
            axref="x", ayref='y',
            ax=pos_subx,
            ay=pos_suby,
            arrowhead=2,
            arrowwidth=0.5,
            arrowcolor=color_bus, )
        )
        figure.add_annotation(arrow_)
        # TODO (pos_subx, pos_suby)  based on bus

        # plot the storage itself
        # TODO add a custom image here
        figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                    mode="markers",
                                    # text=[text],
                                    name=name,
                                    marker=self._marker_storage,
                                    showlegend=False))

        # plot the value (text on the storage)
        if text is not None:
            label_position = self.choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                        text=[text],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False))

    def _one_line(self, name, obs, figure):
        """draw one powerline"""
        # retrieve its id
        id_ = self.ids[name]

        # status
        connected = obs.line_status[id_]

        # coloring
        color = self.line_color_scheme[0]

        # position
        (x_or, y_or), (x_ex, y_ex) = self.layout[name]
        line_style = dict(dash=None if connected else "dash",
                          color=color)

        line_trace = go.Scatter(x=(x_or, x_ex),
                                y=(y_or, y_ex),
                                name=name,
                                line=line_style,
                                hoverinfo='skip',
                                showlegend=False)
        figure.add_trace(line_trace)

        # arrow for the buses
        id_topo_vect = self.grid.line_or_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_busor = self._get_bus_color(this_bus)
        id_topo_vect = self.grid.line_or_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_busex = self._get_bus_color(this_bus)

        # plot the "arrow" to the substation for origin side
        sub_id = self.grid.line_or_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        arrow_ = go.layout.Annotation(dict(
                                x=x_or,
                                y=y_or,
                                xref="x", yref="y",
                                text="",
                                showarrow=True,
                                axref="x", ayref='y',
                                ax=pos_subx,
                                ay=pos_suby,
                                arrowhead=2,
                                arrowwidth=0.5,
                                arrowcolor=color_busor, )
        )
        figure.add_annotation(arrow_)

        # plot the "arrow" to the substation for extremity side
        sub_id = self.grid.line_ex_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        arrow_ = go.layout.Annotation(dict(
                                x=x_ex,
                                y=y_ex,
                                xref="x", yref="y",
                                text="",
                                showarrow=True,
                                axref="x", ayref='y',
                                ax=pos_subx,
                                ay=pos_suby,
                                arrowhead=2,
                                arrowwidth=0.5,
                                arrowcolor=color_busex, )
        )
        figure.add_annotation(arrow_)

        # plot information on the powerline
        # first case: its a information about the all powerline, so i plot it in the middle
        text = None
        if self.line_info == "rho":
            text = f" {100.*obs.rho[id_]:.2f}%"
        elif self.line_info == "name":
            text = name
        elif self.line_info == "th_lim":
            text = f" {obs._thermal_limit[id_]}A"
        elif self.line_info == "cooldown":
            text = f" {obs.time_before_cooldown_line[id_]} "
        elif self.line_info == "timestep_overflow":
            text = f" {obs.timestep_overflow[id_]} "

        if self.line_side == "or" or self.line_side == "ex" or self.line_side == "both":
            # something in the middle of the powerline
            pos_x, pos_y = 0.5 * (x_or + x_ex), 0.5 * (y_or + y_ex)
            label_position = self.choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[pos_x], y=[pos_y],
                                        text=[text],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False))

        # TODO and now each side of the powerline
        if (self.line_side == "or" or self.line_side == "both") and text is None:
            # find which text is displayed
            if self.line_info == "p":
                text_or = f" {obs.p_or[id_]:.2f}MW"
            elif self.line_info == "v":
                text_or = f" {obs.q_or[id_]:.2f}kV"
            elif self.line_info == "q":
                text_or = f" {obs.v_or[id_]:.2f}MVAr"
            elif self.line_info == "a":
                text_or = f" {obs.a_or[id_]:.2f}A"
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line value: {self.line_info}")

            # plot the value (text on the gen)
            label_position = self.choose_label_pos((x_or, y_or), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[x_or], y=[y_or],
                                        text=[text_or],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False))

        if (self.line_side == "ex" or self.line_side == "both") and text is None:
            # find which text is displayed
            if self.line_info == "p":
                text_ex = f" {obs.p_ex[id_]:.2f}MW"
            elif self.line_info == "v":
                text_ex = f" {obs.q_ex[id_]:.2f}MVAr"
            elif self.line_info == "q":
                text_ex = f" {obs.v_ex[id_]:.2f}kV"
            elif self.line_info == "a":
                text_ex = f" {obs.a_ex[id_]:.2f}A"
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line. value: {self.line_info}")

            # plot the value (text on the gen)
            label_position = self.choose_label_pos((x_ex, y_ex), (pos_subx, pos_suby))
            figure.add_trace(go.Scatter(x=[x_ex], y=[y_ex],
                                        text=[text_ex],
                                        mode="text",
                                        name=name,
                                        hoverinfo='skip',
                                        textposition=label_position,
                                        showlegend=False)
                             )
