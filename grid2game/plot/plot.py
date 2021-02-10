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


# https://dash.plotly.com/dash-core-components/graph
# https://dash.plotly.com/interactive-graphing


class PlotParams(object):
    """this is what you need to modify if you want to customize the plots"""
    def __init__(self):
        ### bus color
        self.col_bus1 = "red"
        self.col_bus2 = "blue"
        self.col_deact = "black"

        # width of the line that connects element to bus
        self._line_bus_width = 0.5

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
        self._process_lines_layout()

        # initialize the figures
        self.figure_rt = None
        self.figure_forecat = None
        self.width = 1280
        self.height = 720

        # and the units
        self.line_info = "rho"
        self.line_side = "or"
        self.load_info = "p"
        self.gen_info = "p"
        self.storage_info = "p"

        # need to be initialized
        self.for_trace_sub = {}
        self.for_trace_load = {}
        self.for_trace_gen = {}
        self.for_trace_stor = {}
        self.for_trace_line = {}
        self.rt_trace_sub = {}
        self.rt_trace_load = {}
        self.rt_trace_gen = {}
        self.rt_trace_stor = {}
        self.rt_trace_line = {}
        self.obs_forecast = None
        self.obs_rt = None

    def init_figs(self, obs_rt, obs_forecast):
        """initialized the figures, and draw them"""
        # create once and for all the figures
        self.figure_rt = go.Figure()
        self.figure_forecat = go.Figure()

        self.obs_rt = obs_rt
        self.obs_forecast = obs_forecast

        # init the layout of the stuff (these should be called only once)
        self._init_loads()
        self._init_gens()
        self._init_storages()
        self._init_subs()
        self._init_lines()

        # update the figures with first observations
        # real time figures
        self.update_rt(obs_rt)

        # draw the grid graphs
        self.update_forecat(obs_forecast)

        # set the layout
        self._set_layout(self.figure_rt)
        self._set_layout(self.figure_forecat)

    def update_rt(self, obs_rt):
        """update real time observation both in the values of the dictionary and in the figure"""
        self.obs_rt = obs_rt
        self._update_all_elements(is_forecast=False)
        self._update_all_figures_all_values(forecast_only=False)

    def update_forecat(self, obs_forecast):
        """update forecast observation both in the values of the dictionary and in the figure"""
        self.obs_forecast = obs_forecast
        self._update_all_elements(is_forecast=True)
        self._update_all_figures_all_values(forecast_only=True)

    def _update_all_figures_all_values(self, forecast_only):
        self.update_lines_info(forecast_only)
        self.update_lines_side(forecast_only)
        self.update_loads_info(forecast_only)
        self.update_gens_info(forecast_only)
        self.update_storages_info(forecast_only)

    def update_lines_info(self, forecast_only=False):
        """update the information displayed for powerlines, and updates the traces"""
        if not forecast_only:
            self._update_lines(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_line[trace.name])
                                                         if trace.name in self.rt_trace_line else ())

        self._update_lines(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.rt_trace_line[trace.name])
                                                         if trace.name in self.rt_trace_line else ())

    def update_lines_side(self, forecast_only=False):
        """update the information displayed for powerlines (side), and updates the traces"""

        if not forecast_only:
            self._update_lines(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_line[trace.name])
                                                         if trace.name in self.rt_trace_line else ())

        self._update_lines(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.rt_trace_line[trace.name])
                                                         if trace.name in self.rt_trace_line else ())

    def update_loads_info(self, forecast_only=False):
        """update the information displayed for loads, and updates the traces"""
        if not forecast_only:
            # update the traces containing loads values for the real obs
            self._update_loads(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_load[trace.name])
                                                         if trace.name in self.rt_trace_load else ())

        # update the traces containing loads values for the forecast obs
        self._update_loads(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.for_trace_load[trace.name])
                                                          if trace.name in self.for_trace_load else ())

    def update_gens_info(self, forecast_only=False):
        """update the information displayed for generators, and updates the traces"""

        if not forecast_only:
            self._update_gens(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_gen[trace.name])
                                                         if trace.name in self.rt_trace_gen else ())

        self._update_gens(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.for_trace_gen[trace.name])
                                                         if trace.name in self.for_trace_gen else ())

    def update_storages_info(self, forecast_only=False):
        """update the information displayed for storages, and updates the traces"""
        if not forecast_only:
            self._update_storages(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_stor[trace.name])
                                                         if trace.name in self.rt_trace_stor else ())

        self._update_storages(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.for_trace_stor[trace.name])
                                                         if trace.name in self.for_trace_stor else ())

    def _process_lines_layout(self):
        """compute pos_or and pos_ex of both the extremity of the powerline and update the self.ids"""
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

            zline_or = z_subor + self._sub_radius * cmath.exp(1j * theta_diff)
            zline_ex = z_subor + (r_diff - self._sub_radius) * cmath.exp(1j * theta_diff)
            line_or_pos = zline_or.real, zline_or.imag
            line_ex_pos = zline_ex.real, zline_ex.imag
            self.layout[nm] = (line_or_pos, line_ex_pos)

    def _init_loads(self):
        """add the static load information to the figures and initial load info Should be called only once"""
        trace_load = []
        for nm in self.grid.name_load:
            self._one_load_init(nm, trace_load)
        self.figure_rt.add_traces(trace_load)
        self.figure_forecat.add_traces(trace_load)

        self._update_loads(self.obs_rt, is_forecast=False)
        self._update_loads(self.obs_forecast, is_forecast=True)

    def _init_gens(self):
        """add all the traces for generators on the figure. Should be called only once"""
        traces = []
        for nm in self.grid.name_gen:
            self._one_gen_init(nm, traces)

        self.figure_rt.add_traces(traces)
        self.figure_forecat.add_traces(traces)

    def _init_storages(self):
        """add all the traces for storage units on the figure. Should be called only once"""
        traces = []
        for nm in self.grid.name_storage:
            self._one_storage_init(nm, traces)
        self.figure_rt.add_traces(traces)
        self.figure_forecat.add_traces(traces)

    def _init_lines(self):
        """all the traces for the lines on the figure. Should be called only once"""
        traces = []
        for nm in self.grid.name_line:
            self._one_line_init(nm, traces)
        self.figure_rt.add_traces(traces)
        self.figure_forecat.add_traces(traces)

    def _init_subs(self):
        """all the traces for substation on the figure. Should be called only once"""
        traces = []
        for nm in self.grid.name_sub:
            self._one_sub_init(nm, traces)
        self.figure_rt.add_traces(traces)
        self.figure_forecat.add_traces(traces)

    def _update_subs(self, obs, is_forecast):
        """update the traces for the substation, without updating the figure."""
        if is_forecast:
            # this was a forecast
            self.for_trace_sub = {}
            traces = self.for_trace_sub
        else:
            # this was the real time
            self.rt_trace_sub = {}
            traces = self.for_trace_sub

        for nm in self.grid.name_sub:
            self._one_sub(nm, obs, traces)

    def _update_loads(self, obs, is_forecast):
        """update the traces for the load, without updating the figure."""

        if is_forecast:
            # this was a forecast
            self.for_trace_load = {}
            traces = self.for_trace_load
        else:
            # this was the real time
            self.rt_trace_load = {}
            traces = self.rt_trace_load

        for nm in self.grid.name_load:
            self._one_load(nm, obs, traces)

    def _update_gens(self, obs, is_forecast):
        """update the traces for the generators, without updating the figure."""
        if is_forecast:
            # this was a forecast
            self.for_trace_gen = {}
            traces = self.for_trace_gen
        else:
            # this was the real time
            self.rt_trace_gen = {}
            traces = self.rt_trace_gen

        for nm in self.grid.name_gen:
            self._one_gen(nm, obs, traces)

    def _update_lines(self, obs, is_forecast):
        """update the traces for the lines, without updating the figure."""
        if is_forecast:
            # this was a forecast
            self.for_trace_line = {}
            traces = self.for_trace_line
        else:
            # this was the real time
            self.rt_trace_line = {}
            traces = self.rt_trace_line

        for nm in self.grid.name_line:
            self._one_line(nm, obs, traces)

    def _update_storages(self, obs, is_forecast):
        """update the traces for the storages, without updating the figure."""
        if is_forecast:
            # this was a forecast
            self.for_trace_stor = {}
            traces = self.for_trace_stor
        else:
            # this was the real time
            self.rt_trace_stor = {}
            traces = self.rt_trace_stor

        for nm in self.grid.name_storage:
            self._one_storage(nm, obs, traces)

    def _update_all_elements(self, is_forecast):
        """update the traces for all elements, without updating the figure."""
        obs = self.obs_forecast if is_forecast else self.obs_rt
        self._update_subs(obs, is_forecast)
        self._update_loads(obs, is_forecast)
        self._update_gens(obs, is_forecast)
        self._update_lines(obs, is_forecast)
        self._update_storages(obs, is_forecast)

    def _set_layout(self, fig):
        """set the layout of the figure, for now called only once"""
        fig.update_layout(width=self.width,
                          height=self.height,
                          xaxis=dict(visible=False),
                          yaxis=dict(visible=False),
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=0, r=0, b=0, t=0, pad=0),
                          )

    def _one_sub_init(self, name, traces):
        """draw one substation"""
        # find position
        (pos_x, pos_y) = self.layout[name]

        # plot the substation itself
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          mode="markers",
                          # text=[text],
                          name=name,
                          marker=self._marker_sub,
                          showlegend=False)
        traces.append(tmp_)

    def _one_sub(self, name, obs, dict_traces):
        """draw one substation"""
        pass
        # plot the topology (circle for the busbars)
        # TODO

    @staticmethod
    def _choose_label_pos(my_pos, sub_pos):
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

    def _one_load_init(self, name, traces):
        # find its position
        (pos_x, pos_y) = self.layout[name]

        # retrieve its id
        id_ = self.ids[name]

        # plot the load itself
        # TODO add a custom image here for example a house
        tmp_ = go.Scatter(x=[pos_x], y=[pos_y],
                          mode="markers",
                          # text=[text],
                          name=name+"_img",
                          marker=self._marker_load,
                          showlegend=False)
        traces.append(tmp_)

        # plot the "arrow" to the substation
        color_bus = self.col_bus1
        sub_id = self.grid.load_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        to_sub = go.Scatter(x=(pos_x, pos_subx),
                            y=(pos_y, pos_suby),
                            name=name+"_bus",
                            hoverinfo='skip',
                            showlegend=False,
                            mode='lines',
                            line=dict(color=color_bus, width=self._line_bus_width)
                            )
        traces.append(to_sub)

        # value displayed on the load
        text = "text"
        label_position = self._choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[pos_x], y=[pos_y],
                          text=[text],
                          mode="text",
                          name=name+"_val",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

    def _one_load(self, name, obs, dict_traces):
        """draw one load"""
        res_anot, res_trace = [], []

        # retrieve its id
        id_ = self.ids[name]

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
        dict_traces[name+"_bus"] = {"line": dict(color=color_bus, width=self._line_bus_width)}

        # plot the value (text on the load)
        if text is None:
            text = ""
        dict_traces[name+"_val"] = {"text": [text]}

    def _one_gen_init(self, name, traces):
        """find position of static gen information"""
        # find position
        (pos_x, pos_y) = self.layout[name]

        # retrieve its id
        id_ = self.ids[name]

        # plot the gen itself
        # TODO add a custom image here depending on the type of the generator, wind, solar, etc.
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          mode="markers",
                          # text=[text],
                          name=name+"_img",
                          marker=self._marker_gen,
                          showlegend=False)
        traces.append(tmp_)

        # plot the "arrow" to the substation
        color_bus = self.col_bus1
        sub_id = self.grid.gen_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        to_sub = go.Scatter(x=(pos_x, pos_subx),
                            y=(pos_y, pos_suby),
                            name=name+"_bus",
                            hoverinfo='skip',
                            showlegend=False,
                            mode='lines',
                            line=dict(color=color_bus, width=self._line_bus_width)
                            )
        traces.append(to_sub)

        text = ""
        label_position = self._choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          text=[text],
                          mode="text",
                          name=name+"_val",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

    def _one_gen(self, name, obs, dict_traces):
        """draw one generator"""
        res_anot, res_trace = [], []

        # retrieve its id
        id_ = self.ids[name]

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
        dict_traces[name + "_bus"] = {"line": dict(color=color_bus, width=self._line_bus_width)}

        # plot the value (text on the gen)
        if text is None:
            text = ""
        dict_traces[name+"_val"] = {"text": [text]}
        return res_anot, res_trace

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

    def _one_storage_init(self, name, traces):
        """find position of static storage information"""
        # find position
        (pos_x, pos_y) = self.layout[name]

        # retrieve its id
        id_ = self.ids[name]

        # plot the storage itself
        # TODO add a custom image here
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          mode="markers",
                          # text=[text],
                          name=name+"_img",
                          marker=self._marker_storage,
                          showlegend=False)
        traces.append(tmp_)

        # plot the "arrow" to the substation
        color_bus = self.col_bus1
        sub_id = self.grid.storage_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        to_sub = go.Scatter(x=(pos_x, pos_subx),
                            y=(pos_y, pos_suby),
                            name=name+"_bus",
                            hoverinfo='skip',
                            showlegend=False,
                            mode='lines',
                            line=dict(color=color_bus, width=self._line_bus_width)
                            )
        traces.append(to_sub)

        # text displayed on the storage
        text = ""
        label_position = self._choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          text=[text],
                          mode="text",
                          name=name+"_val",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

    def _one_storage(self, name, obs, dict_traces):
        """draw one storage unit"""
        # retrieve its id
        id_ = self.ids[name]

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
        dict_traces[name + "_bus"] = {"line": dict(color=color_bus, width=self._line_bus_width)}

        # plot the value (text on the storage)
        if text is None:
            text = ""
        dict_traces[name+"_val"] = {"text": [text]}

    def _one_line_init(self, name, traces):

        # retrieve its id
        id_ = self.ids[name]

        # position
        connected = True
        color = self.line_color_scheme[0]

        (x_or, y_or), (x_ex, y_ex) = self.layout[name]
        line_style = dict(dash=None if connected else "dash",
                          color=color)
        # TODO color depending on value plotted !
        line_trace = go.Scatter(x=(x_or, x_ex),
                                y=(y_or, y_ex),
                                name=name+"_img",
                                line=line_style,
                                hoverinfo='skip',
                                showlegend=False)
        # figure.add_trace(line_trace)
        traces.append(line_trace)

        # plot the "arrow" to the substation for origin side
        color_busor = self.col_bus1
        sub_id = self.grid.line_or_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        to_sub = go.Scatter(x=(x_or, pos_subx),
                            y=(y_or, pos_suby),
                            name=name+"_bus",
                            hoverinfo='skip',
                            showlegend=False,
                            mode='lines',
                            line=dict(color=color_busor, width=self._line_bus_width)
                            )
        traces.append(to_sub)

        # plot the "arrow" to the substation for extremity side
        color_busex = self.col_bus1
        sub_id = self.grid.line_ex_to_subid[id_]
        sub_name = self.grid.name_sub[sub_id]
        pos_subx, pos_suby = self.layout[sub_name]
        to_sub = go.Scatter(x=(x_ex, pos_subx),
                            y=(y_ex, pos_suby),
                            name=name+"_bus",
                            hoverinfo='skip',
                            showlegend=False,
                            mode='lines',
                            line=dict(color=color_busex, width=self._line_bus_width)  # TODO
                            )
        traces.append(to_sub)

        # text in the middle of the powerline
        text = ""
        pos_x, pos_y = 0.5 * (x_or + x_ex), 0.5 * (y_or + y_ex)
        label_position = self._choose_label_pos((pos_x, pos_y), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[pos_x],
                          y=[pos_y],
                          text=[text],
                          mode="text",
                          name=name+"_value",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

        # text on the origin side
        text_or = ""
        label_position = self._choose_label_pos((x_or, y_or), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[x_or],
                          y=[y_or],
                          text=[text_or],
                          mode="text",
                          name=name+"_value_or",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

        # text on the extremity side
        text_ex = ""
        label_position = self._choose_label_pos((x_ex, y_ex), (pos_subx, pos_suby))
        tmp_ = go.Scatter(x=[x_ex], y=[y_ex],
                          text=[text_ex],
                          mode="text",
                          name=name+"_value_ex",
                          hoverinfo='skip',
                          textposition=label_position,
                          showlegend=False)
        traces.append(tmp_)

    def _one_line(self, name, obs, dict_traces):
        """draw one powerline"""
        # retrieve its id
        id_ = self.ids[name]

        # status
        connected = obs.line_status[id_]

        # coloring
        color = self.line_color_scheme[0]

        # position
        line_style = dict(dash=None if connected else "dash",
                          color=color)
        dict_traces[name+"_img"] = {"line": line_style}

        # arrow for the buses
        id_topo_vect = self.grid.line_or_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_busor = self._get_bus_color(this_bus)
        id_topo_vect = self.grid.line_or_pos_topo_vect[id_]
        this_bus = obs.topo_vect[id_topo_vect]
        color_busex = self._get_bus_color(this_bus)

        # plot the "arrow" to the substation for origin side
        dict_traces[name + "_bus"] = {"line": dict(color=color_busor, width=self._line_bus_width)}

        # plot the "arrow" to the substation for extremity side
        dict_traces[name + "_bus"] = {"line": dict(color=color_busex, width=self._line_bus_width)}

        # plot texts on the powerline
        # text in the middle
        text = ""
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
        elif self.line_info == "none":
            text = ""
        dict_traces[name+"_value"] = {"text": [text]}

        # text origin side
        text_or = ""
        if (self.line_side == "or" or self.line_side == "both") and text == "":
            # find which text is displayed
            if self.line_info == "p":
                text_or = f" {obs.p_or[id_]:.2f}MW"
            elif self.line_info == "v":
                text_or = f" {obs.q_or[id_]:.2f}kV"
            elif self.line_info == "q":
                text_or = f" {obs.v_or[id_]:.2f}MVAr"
            elif self.line_info == "a":
                text_or = f" {obs.a_or[id_]:.2f}A"
            elif self.line_info == "none":
                pass
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line value for or side: {self.line_info}")
        dict_traces[name+"_value_or"] = {"text": [text_or]}

        # text extremity side
        text_ex = ""
        if (self.line_side == "ex" or self.line_side == "both") and text == "":
            # find which text is displayed
            if self.line_info == "p":
                text_ex = f" {obs.p_ex[id_]:.2f}MW"
            elif self.line_info == "v":
                text_ex = f" {obs.q_ex[id_]:.2f}MVAr"
            elif self.line_info == "q":
                text_ex = f" {obs.v_ex[id_]:.2f}kV"
            elif self.line_info == "a":
                text_ex = f" {obs.a_ex[id_]:.2f}A"
            elif self.line_info == "none":
                pass
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line value for ex side: {self.line_info}")
        dict_traces[name+"_value_ex"] = {"text": [text_ex]}
