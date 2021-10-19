# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import cmath
import warnings
import time
import plotly.graph_objects as go

from grid2op.PlotGrid import PlotPlotly
from grid2op.Space import GridObjects

from grid2game.plot.plot_param import PlotParams

# https://dash.plotly.com/dash-core-components/graph
# https://dash.plotly.com/interactive-graphing


class PlotGrids(PlotParams):
    def __init__(self, observation_space):
        super().__init__()
        self.glop_plot = PlotPlotly(observation_space)
        self.observation_space = observation_space
        self.grid = GridObjects.init_grid(observation_space)

        # process the layout (position of everything)
        self.layout = self.glop_plot._grid_layout
        self.ids = {nm: id_ for id_, nm in enumerate(self.grid.name_load)}
        self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_gen)})
        if hasattr(self.grid, "name_storage"):
            self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_storage)})
        else:
            warnings.warn("Please use grid2op >= 1.5", DeprecationWarning)
        self.ids.update({nm: id_ for id_, nm in enumerate(self.grid.name_sub)})
        self._process_lines_layout()

        # initialize the figures
        self.figure_rt = None
        self.figure_forecat = None
        self.sub_fig = None
        self._last_sub_clicked = None
        self.figs_substation_zoomed = []
        self.objs_info_zoomed = {}

        # and the units
        # self.line_info = "rho"
        # self.line_side = "or"
        # self.load_info = "p"
        # self.gen_info = "p"
        # self.storage_info = "p"
        self.line_info = "none"
        self.line_side = "none"
        self.load_info = "none"
        self.gen_info = "none"
        self.storage_info = "none"

        # converter for the clickable objects (for position to clickable stuff)
        self.pos_to_object = {}
        for sub_id, name in enumerate(self.grid.name_sub):
            self.pos_to_object[tuple(self.layout[name])] = ("sub", name, sub_id)
        for gen_id, name in enumerate(self.grid.name_gen):
            self.pos_to_object[tuple(self.layout[name])] = ("gen", name, gen_id)
        if hasattr(self.grid, "name_storage"):
            for stor_id, name in enumerate(self.grid.name_storage):
                self.pos_to_object[tuple(self.layout[name])] = ("stor", name, stor_id)
        for line_id, name in enumerate(self.grid.name_line):
            (x_or, y_or), (x_ex, y_ex) = self.layout[name]
            x_mid = int((x_or + x_ex) / 2)
            y_mid = int((y_or + y_ex) / 2)
            self.pos_to_object[(x_mid, y_mid)] = ("line", name, line_id)

        # need to be initialized
        self.for_trace_datetime = {}
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
        self.rt_trace_datetime = {}
        self.obs_forecast = None
        self.obs_rt = None

        # for zoom in substation
        # TODO check that !
        self._r_sub_zoom = 60
        self._dist_bus_1 = 0.6  # as fraction of the _r_sub_zoom
        self._dist_bus_2 = 0.8  # as fraction of the _r_sub_zoom
        self._dist_zoomed_in = 1.5  # as fraction of the _r_sub_zoom
        self.style_bus1 = "dash"
        self.style_bus2 = 'dot'

        # timers
        self._time_update_rt = 0.
        self._time_update_for = 0.

        # remember the last plotted observation
        self._last_rt_step = -1
        self._last_for_step = -1

    def _add_element_to_sub(self, nm_this_obj, posx, posy, marker, fig,
                            pos_obj, pos_in_sub, pos_in_topo_vect,
                            line_side=None):
        """add an element when a substation is zoomed in"""
        if line_side is None:
            tmp_x, tmp_y = self.layout[nm_this_obj]  # init position of the element
        elif line_side == "or":
            (tmp_x, tmp_y), _ = self.layout[nm_this_obj]  # init position of the element
        elif line_side == "ex":
            _, (tmp_x, tmp_y) = self.layout[nm_this_obj]  # init position of the element
        else:
            raise RuntimeError(f"Unrecognized line side {line_side}, should be \"or\" or \"ex\"")

        dist_center = cmath.sqrt((tmp_x - posx) ** 2 + (tmp_y - posy) ** 2)
        dist_center = dist_center.real
        my_dist = self._dist_zoomed_in * self._r_sub_zoom
        tmp_x = int(posx + my_dist / dist_center * (tmp_x - posx))
        tmp_y = int(posy + my_dist / dist_center * (tmp_y - posy))
        # compute intersection with the circles representing the buses
        posx_bus1 = int(posx + self._dist_bus_1 / self._dist_zoomed_in * (tmp_x - posx))
        posy_bus1 = int(posy + self._dist_bus_1 / self._dist_zoomed_in * (tmp_y - posy))
        posx_bus2 = int(posx + self._dist_bus_2 / self._dist_zoomed_in * (tmp_x - posx))
        posy_bus2 = int(posy + self._dist_bus_2 / self._dist_zoomed_in * (tmp_y - posy))
        # dict to map coordinate to objects
        pos_obj[(tmp_x, tmp_y)] = (nm_this_obj, "obj", pos_in_sub, pos_in_topo_vect)
        pos_obj[(posx_bus1, posy_bus1)] = (nm_this_obj, "bus1", pos_in_sub, pos_in_topo_vect)
        pos_obj[(posx_bus2, posy_bus2)] = (nm_this_obj, "bus2", pos_in_sub, pos_in_topo_vect)
        # dict to map object to their coordinates
        if line_side is None:
            self.objs_info_zoomed[nm_this_obj] = ((tmp_x, tmp_y), (posx_bus1, posy_bus1), (posx_bus2, posy_bus2))
        elif line_side == "ex":
            self.objs_info_zoomed[nm_this_obj+"_ex"] = ((tmp_x, tmp_y), (posx_bus1, posy_bus1), (posx_bus2, posy_bus2))
        elif line_side == "or":
            self.objs_info_zoomed[nm_this_obj+"_or"] = ((tmp_x, tmp_y), (posx_bus1, posy_bus1), (posx_bus2, posy_bus2))

        # draw everything
        tmp_ = go.Scatter(x=[tmp_x], y=[tmp_y],
                          mode="markers",
                          name=nm_this_obj,
                          marker=marker,
                          showlegend=False)
        fig.add_trace(tmp_)
        tmp_ = go.Scatter(x=[posx_bus1], y=[posy_bus1],
                          mode="markers",
                          name=nm_this_obj + "_bus1",
                          marker=self._marker_bus1,
                          showlegend=False)
        fig.add_trace(tmp_)
        tmp_ = go.Scatter(x=[posx_bus2], y=[posy_bus2],
                          mode="markers",
                          name=nm_this_obj + "_bus2",
                          marker=self._marker_bus2,
                          showlegend=False)
        fig.add_trace(tmp_)

        # line that connected the bus to the object
        tmp = go.Scatter(x=[tmp_x, posx_bus1],
                         y=[tmp_y, posy_bus1],
                         mode="lines",
                         name=nm_this_obj+"_current_bus",
                         showlegend=False,
                         line=dict(color=self.col_bus1, dash=self.style_bus1)
                         )
        fig.add_trace(tmp)

    def _init_figures_substation_zoomed(self):
        """init all the figures for the substation, when zoomed in"""
        self.figs_substation_zoomed = []
        for sub_id, sub_name in enumerate(self.grid.name_sub):
            tmp_fig = go.Figure()
            (posx, posy) = self.layout[sub_name]
            tmp_fig.add_shape(type="circle",
                              xref="x", yref="y",
                              fillcolor=self._sub_fill_color,
                              x0=posx - self._r_sub_zoom,
                              y0=posy - self._r_sub_zoom,
                              x1=posx + self._r_sub_zoom,
                              y1=posy + self._r_sub_zoom,
                              line_color=self._sub_fill_color,
                              opacity=0.5
                              )
            tmp_fig.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=posx - self._dist_bus_1 * self._r_sub_zoom,
                              y0=posy - self._dist_bus_1 * self._r_sub_zoom,
                              x1=posx + self._dist_bus_1 * self._r_sub_zoom,
                              y1=posy + self._dist_bus_1 * self._r_sub_zoom,
                              line=dict(color=self.col_bus1, dash=self.style_bus1)
                              )
            tmp_fig.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=posx - self._dist_bus_2 * self._r_sub_zoom,
                              y0=posy - self._dist_bus_2 * self._r_sub_zoom,
                              x1=posx + self._dist_bus_2 * self._r_sub_zoom,
                              y1=posy + self._dist_bus_2 * self._r_sub_zoom,
                              line=dict(color=self.col_bus2, dash=self.style_bus2)
                              )
            tmp_fig.add_trace(go.Scatter(x=[posx],
                                         y=[posy],
                                         text=[sub_name],
                                         mode="text",
                                         name=sub_name,
                                         showlegend=False
                                         ))

            pos_objs = {}
            # draw the objects connected to it
            # dict_ = self.grid.get_obj_connect_to(substation_id=obj_id)  # TODO weird bug
            dict_ = self.observation_space.get_obj_connect_to(substation_id=sub_id)
            for load_id in dict_["loads_id"]:
                nm_this_obj = self.grid.name_load[load_id]
                pos_in_sub = self.grid.load_to_sub_pos[load_id]
                pos_topo_vect = self.grid.load_pos_topo_vect[load_id]
                self._add_element_to_sub(nm_this_obj, posx, posy, self._marker_load,
                                         tmp_fig, pos_objs, pos_in_sub, pos_topo_vect)
            for gen_id in dict_["generators_id"]:
                nm_this_obj = self.grid.name_gen[gen_id]
                pos_in_sub = self.grid.gen_to_sub_pos[gen_id]
                pos_topo_vect = self.grid.gen_pos_topo_vect[gen_id]
                self._add_element_to_sub(nm_this_obj, posx, posy, self._marker_gen,
                                         tmp_fig, pos_objs, pos_in_sub, pos_topo_vect)
            for line_id in dict_["lines_or_id"]:
                nm_this_obj = self.grid.name_line[line_id]
                pos_in_sub = self.grid.line_or_to_sub_pos[line_id]
                pos_topo_vect = self.grid.line_or_pos_topo_vect[line_id]
                self._add_element_to_sub(nm_this_obj, posx, posy, self._marker_line, tmp_fig,
                                         pos_objs, pos_in_sub, pos_topo_vect, "or")
            for line_id in dict_["lines_ex_id"]:
                nm_this_obj = self.grid.name_line[line_id]
                pos_in_sub = self.grid.line_ex_to_sub_pos[line_id]
                pos_topo_vect = self.grid.line_ex_pos_topo_vect[line_id]
                self._add_element_to_sub(nm_this_obj, posx, posy, self._marker_line, tmp_fig,
                                         pos_objs, pos_in_sub, pos_topo_vect, "ex")
            if "storages_id" in dict_:
                # storage units were introduced in grid2op 1.5, this is a "if" for backward compatibility
                for stor_id in dict_["storages_id"]:
                    nm_this_obj = self.grid.name_storage[stor_id]
                    pos_in_sub = self.grid.storage_to_sub_pos[stor_id]
                    pos_topo_vect = self.grid.storage_pos_topo_vect[stor_id]
                    self._add_element_to_sub(nm_this_obj, posx, posy, self._marker_storage,
                                             tmp_fig, pos_objs, pos_in_sub, pos_topo_vect)
            tmp_fig.layout.update({
                                   "xaxis": {'visible': False},
                                   "yaxis": {'visible': False},
                                   "margin": dict(l=0, r=0, t=0, b=0)}
                                  )
            self.figs_substation_zoomed.append((tmp_fig, pos_objs))

    def retrieve_obj_info(self, obj_info):
        if obj_info[self.grid.LOA_COL] != -1:
            obj_id = obj_info[self.grid.LOA_COL]
            nm_this_obj = self.grid.name_load[obj_id]
            (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = \
                self.objs_info_zoomed[nm_this_obj]
        elif obj_info[self.grid.GEN_COL] != -1:
            obj_id = obj_info[self.grid.GEN_COL]
            nm_this_obj = self.grid.name_gen[obj_id]
            (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = \
                self.objs_info_zoomed[nm_this_obj]
        elif obj_info[self.grid.STORAGE_COL] != -1:
            obj_id = obj_info[self.grid.STORAGE_COL]
            nm_this_obj = self.grid.name_storage[obj_id]
            (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = \
                self.objs_info_zoomed[nm_this_obj]
        elif obj_info[self.grid.LOR_COL] != -1:
            obj_id = obj_info[self.grid.LOR_COL]
            nm_this_obj = self.grid.name_line[obj_id]
            (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = \
                self.objs_info_zoomed[nm_this_obj+"_or"]
        elif obj_info[self.grid.LEX_COL] != -1:
            obj_id = obj_info[self.grid.LEX_COL]
            nm_this_obj = self.grid.name_line[obj_id]
            (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = \
                self.objs_info_zoomed[nm_this_obj+"_ex"]
        else:
            raise RuntimeError("Unknown element in the substation. Have your forgotten to had a "
                               "case in the retrieve_obj_info function that handles "
                               "grid2op.Spaces.grid_objects_types ?")
        return nm_this_obj, (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2)

    def get_object_clicked_sub(self, clickData):
        """handles which object is clicked on when a substation is being zoomed in"""
        _, dict_sub = self.figs_substation_zoomed[self._last_sub_clicked]
        res = (None, 0)
        if clickData is not None:
            pts = clickData['points'][0]
            pos_clicked = (int(pts["x"]), int(pts["y"]))
            if pos_clicked in dict_sub:
                (nm_this_obj, what_clicked, pos_in_sub, pos_in_topo_vect) = dict_sub[pos_clicked]
                res = (pos_in_topo_vect, -1 if what_clicked == "obj" else (1 if what_clicked == "bus1" else 2))
        return res

    def _get_res_sub_clicked(self, obj_id):
        # draw the substation
        self.sub_fig, _ = self.figs_substation_zoomed[obj_id]
        self._last_sub_clicked = obj_id

        # add the right color to which the object is connected
        current_topo = self.obs_rt.sub_topology(obj_id)
        objs_this_sub = self.obs_rt.get_obj_substations(substation_id=obj_id)
        for obj_info, obj_bus in zip(objs_this_sub, current_topo):
            nm_this_obj, (x_this_obj, y_this_obj), (xbus1, ybus1), (xbus2, ybus2) = self.retrieve_obj_info(obj_info)
            line_style = dict(color=self.col_bus1, dash=self.style_bus1)
            bus_x = xbus1
            bus_y = ybus1
            if obj_bus == 2:
                line_style = dict(color=self.col_bus2, dash=self.style_bus2)
                bus_x = xbus2
                bus_y = ybus2
            self.sub_fig.update_traces(x=[x_this_obj, bus_x],
                                       y=[y_this_obj, bus_y],
                                       line=line_style,
                                       selector=dict(name=nm_this_obj + "_current_bus"))
        res_type = (f"Substation id {obj_id}",
                    self.sub_fig
                    )
        return res_type

    def _get_res_line_clicked(self, obj_name, obj_id):
        res_type = (f"Line id {obj_id} ({obj_name})",
                    "0",
                    f"Flow: {self.obs_rt.a_or[obj_id]:.2f}A "
                    f"(thermal limit {self.obs_rt._thermal_limit[obj_id]:.2f}A)"
                    )
        return res_type

    def _get_res_storage_clicked(self, obj_name, obj_id):
        res_type = (f"Storage unit id {obj_id} ({obj_name})",
                    -self.grid.storage_max_p_prod[obj_id],  # TODO use storage_emin
                    self.grid.storage_max_p_absorb[obj_id],  # TODO use storage_emax
                     0.,
                     f"Actual consumption : {self.obs_rt.storage_power[obj_id]:.2f}MW ",
                     f"Actual capacity: {self.obs_rt.storage_charge[obj_id]:.2f}MWh (min: {self.obs_rt.storage_Emin[obj_id]}, max: {self.obs_rt.storage_Emax[obj_id]})",
                     )
        return res_type

    def _get_res_gen_clicked(self, obj_name, obj_id):
        # so obj_type == "gen":
        if self.grid.gen_renewable[obj_id]:
            # renewable generator => curtailment
            min_ = 0.
            # i do the curtailment th i can: 100% = curtail all the actual production
            max_ = 1.0 * self.obs_rt.gen_pmax[obj_id]
            val_ = self.obs_rt.prod_p[obj_id] - 1.0 * self.obs_rt.curtailment_mw[obj_id]
            str_1_ = f"Pmax (after curtail): {self.obs_rt.curtailment_limit_mw[obj_id]:.2f} MW " \
                     f"(real Pmax: {self.obs_rt.gen_pmax[obj_id]:.2f}MW)"
            str_2_ = f"Amount curtail: {self.obs_rt.curtailment_mw[obj_id]:.2f} MW"
            tmp_ = 100.
            if self.obs_rt.prod_p[obj_id] > 0 or self.obs_rt.curtailment_mw[obj_id] > 0:
                tmp_ = (100. * self.obs_rt.prod_p[obj_id] / (
                        self.obs_rt.prod_p[obj_id] + self.obs_rt.curtailment_mw[obj_id]))
            prod_str_ = f"prod : {self.obs_rt.prod_p[obj_id]:.2f}MW " \
                        f"({100. * self.obs_rt.prod_p[obj_id] / self.obs_rt.gen_pmax[obj_id]:.0f}% " \
                        f"of Pmax) " \
                        f"({tmp_:.0f} % of what's possible)"
        else:
            # standard generator => redispatching
            min_ = -self.grid.gen_max_ramp_down[obj_id]
            max_ = self.grid.gen_max_ramp_up[obj_id]
            val_ = 0.
            str_1_ = f"dispatch (target): {self.obs_rt.target_dispatch[obj_id]:.2f}MW"
            str_2_ = f"dispatch (actual): {self.obs_rt.actual_dispatch[obj_id]:.2f}MW"
            prod_str_ = f"prod : {self.obs_rt.prod_p[obj_id]:.2f}MW (min: {self.obs_rt.gen_pmin[obj_id]}, max: {self.obs_rt.gen_pmax[obj_id]})"
        res_type = (f"Generator id {obj_id} ({obj_name}, {self.grid.gen_type[obj_id]})",
                    min_,  # TODO use gen_pmin [ie something like min(-gen_pmin, gen_max_ramp_down) ]
                    max_,  # TODO use gen_pmax
                    val_,
                    prod_str_,
                    str_1_,
                    str_2_,
                    )
        return res_type

    def get_object_clicked(self, clickData):
        """return the proper information when the main graph is clicked.

        These information are then used to build the action "manually" by clicking on the things
        """
        # TODO refactor all that to split it into different functions...

        # TODO not sure it's best suited here !
        obj_type = None
        obj_id = None
        res_type = tuple()
        if clickData is not None:
            pts = clickData['points'][0]
            pos_clicked = (int(pts["x"]), int(pts["y"]))
            if pos_clicked in self.pos_to_object:
                (obj_type, obj_name, obj_id) = self.pos_to_object[pos_clicked]
                if obj_type == "sub":
                    res_type = self._get_res_sub_clicked(obj_id)
                elif obj_type == "line":
                    res_type = self._get_res_line_clicked(obj_name, obj_id)
                elif obj_type == "stor":
                    res_type = self._get_res_storage_clicked(obj_name, obj_id)
                else:
                    res_type = self._get_res_gen_clicked(obj_name, obj_id)
        return obj_type, obj_id, res_type

    def init_figs(self, obs_rt, obs_forecast):
        """initialized the figures, and draw them"""
        # create once and for all the figures
        self.figure_rt = go.Figure()
        self.figure_forecat = go.Figure()
        self.sub_fig = go.Figure()

        # to initialized the zoomed in substations layout
        self._init_figures_substation_zoomed()

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

    def update_rt(self, obs_rt, env=None):
        """update real time observation both in the values of the dictionary and in the figure"""
        if env is not None and not env.do_i_display():
            # display of the temporal figures should not be updated (for example because i run the episode
            # until the end)
            return
        beg_ = time.time()
        self._last_rt_time = obs_rt.current_step
        self.obs_rt = obs_rt
        self._update_all_elements(is_forecast=False)
        self._update_all_figures_all_values(forecast_only=False)
        tmp = time.time() - beg_
        self._time_update_rt += tmp
        # print(f'grid (main): {tmp}')

    def update_forecat(self, obs_forecast, env=None):
        """update forecast observation both in the values of the dictionary and in the figure"""
        if env is not None and not env.do_i_display():
            # display of the temporal figures should not be updated (for example because i run the episode
            # until the end)
            return
        beg_ = time.time()
        self._last_for_step = obs_forecast.current_step
        self.obs_forecast = obs_forecast
        self._update_all_elements(is_forecast=True)
        self._update_all_figures_all_values(forecast_only=True)
        tmp = time.time() - beg_
        self._time_update_for += tmp
        # print(f'grid (forecast): {tmp}')

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
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.for_trace_line[trace.name])
                                                         if trace.name in self.for_trace_line else ())

    def update_lines_side(self, forecast_only=False):
        """update the information displayed for powerlines (side), and updates the traces"""

        if not forecast_only:
            self._update_lines(self.obs_rt, is_forecast=False)
            self.figure_rt.for_each_trace(lambda trace: trace.update(**self.rt_trace_line[trace.name])
                                                         if trace.name in self.rt_trace_line else ())

        self._update_lines(self.obs_forecast, is_forecast=True)
        self.figure_forecat.for_each_trace(lambda trace: trace.update(**self.for_trace_line[trace.name])
                                                         if trace.name in self.for_trace_line else ())

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
        if hasattr(self.grid, "name_storage"):
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
        if hasattr(self.grid, "name_storage"):
            # "if" for backward compatibility with grid2op < 1.5
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
        # TODO this is not perfect for now
        # use the "angle"  between the substation and the object itself.
        my_x, my_y = my_pos
        s_x, s_y = sub_pos
        res = "middle center"
        if my_x > s_x and my_y > s_y:
            res = 'top center'
        elif my_x <= s_x and my_y > s_y:
            res = 'middle right'
        elif my_x > s_x and my_y <= s_y:
            res = 'bottom center'
        elif my_x <= s_x and my_y <= s_y:
            res = 'middle left'
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
                          hoverinfo='skip',  # load are not clickable
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
        color = self.line_color_ok

        (x_or, y_or), (x_ex, y_ex) = self.layout[name]
        line_style = dict(dash=None if connected else "dash",
                          color=color)
        # TODO color depending on value plotted !
        line_trace = go.Scatter(x=(x_or, x_ex),
                                y=(y_or, y_ex),
                                name=name+"_img",
                                line=line_style,
                                hoverinfo='skip',
                                mode='lines',
                                showlegend=False)
        # figure.add_trace(line_trace)
        traces.append(line_trace)

        # middle of the line (clickable)
        line_trace = go.Scatter(x=[int((x_or + x_ex)/2)],  # need to adjust pos_to_object above if you change this
                                y=[int((y_or + y_ex)/2)],   # need to adjust pos_to_object above if you change this
                                name=name+"_click",
                                line=line_style,
                                # hoverinfo='skip',
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
        rho = obs.rho[id_]
        color = self.line_color_ok
        width = 1
        # TODO handle line color differently
        if rho > 1.0:
            color = "darkred"
            width = 3
        elif rho > 0.95:
            color = "red"
        elif rho > 0.90:
            color = "coral"
        elif rho > 0.85:
            color = "orange red"
        elif rho > 0.75:
            color = "orange"
        elif rho > 0.50:
            color = "darkblue"

        line_style = dict(dash=None if connected else "dash",
                          color=color, width=width)
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
            text = f" {obs._thermal_limit[id_]:.0f}A"
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
                text_or = f" {obs.v_or[id_]:.2f}kV"
            elif self.line_info == "q":
                text_or = f" {obs.q_or[id_]:.2f}MVAr"
            elif self.line_info == "a":
                text_or = f" {obs.a_or[id_]:.2f}A"
            elif self.line_info == "none":
                pass
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line value for or side info : {self.line_info}")
        dict_traces[name+"_value_or"] = {"text": [text_or]}

        # text extremity side
        text_ex = ""
        if (self.line_side == "ex" or self.line_side == "both") and text == "":
            # find which text is displayed
            if self.line_info == "p":
                text_ex = f" {obs.p_ex[id_]:.2f}MW"
            elif self.line_info == "q":
                text_ex = f" {obs.q_ex[id_]:.2f}MVAr"
            elif self.line_info == "v":
                text_ex = f" {obs.v_ex[id_]:.2f}kV"
            elif self.line_info == "a":
                text_ex = f" {obs.a_ex[id_]:.2f}A"
            elif self.line_info == "none":
                pass
            # TODO handle some "diff" here based on previous time stamps
            else:
                raise RuntimeError(f"Unsupported line value for ex side info : {self.line_info}")
        dict_traces[name+"_value_ex"] = {"text": [text_ex]}
