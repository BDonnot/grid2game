# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import plotly.colors as pc
import plotly.graph_objects as go
import time

try:
    from grid2op.PlotGrid.config import NUKE_COLOR, THERMAL_COLOR, WIND_COLOR, SOLAR_COLOR, HYDRO_COLOR
except ImportError as exc_:
    NUKE_COLOR = "#e5cd00"
    THERMAL_COLOR = "#7e52a0"
    WIND_COLOR = "#71cdb8"
    SOLAR_COLOR = "#d66b0d"
    HYDRO_COLOR = "#1f73b5"
    import warnings
    warnings.warn("Please upgrade to grid2op >= 1.5 to benefit from latest grid2op features. This package might "
                  "not work with grid2op < 1.5",
                  DeprecationWarning)

from grid2game.plot.plot_param import PlotParams


class PlotTemporalSeries(object):
    def __init__(self, tree):
        # super().__init__()

        # maybe in the parameters
        self.color_nuclear = NUKE_COLOR
        self.color_thermal = THERMAL_COLOR
        self.color_wind = WIND_COLOR
        self.color_solar = SOLAR_COLOR
        self.color_hydro = HYDRO_COLOR
        self.color_load = "black"
        self.color_import_export = "gray"

        # height
        self.height = 500

        self.fig_load_gen = None
        self.fig_line_cap = None
        self.init_figures(tree)
        self._timer_update = 0.

    def init_figures(self, tree):
        self.fig_load_gen = go.Figure()
        self.fig_line_cap = go.Figure()

        self.init_traces(tree)

    def update_layout_height(self):
        self.fig_line_cap.update_layout(height=int(self.height))
        self.fig_load_gen.update_layout(height=int(self.height))

    def init_traces(self, tree):
        data = tree.temporal_data
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._max_line_flow,
                          mode="lines",
                          name="Highest line capacity",
                          line=dict(color="red"),
                          showlegend=True)
        self.fig_line_cap.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._secondmax_line_flow,
                          mode="lines",
                          name="2nd highest line cap.",
                          line=dict(color="crimson"),
                          showlegend=True)
        self.fig_line_cap.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._thirdmax_line_flow,
                          mode="lines",
                          name="3rd highest line cap.",
                          line=dict(color="coral"),
                          showlegend=True)
        self.fig_line_cap.add_trace(tmp_)
        tmp_ = go.Scatter(x=(data._datetimes[0], data._datetimes[-1]),
                          y=(1., 1.),
                          mode="lines",
                          name="Overflow limit",
                          hoverinfo='skip',
                          showlegend=True,
                          line=dict(color="darkred", dash="dash", width=2))
        self.fig_line_cap.add_trace(tmp_)
        self.fig_line_cap.update_layout(title={'text': "Line capacity"},
                                        xaxis_title='date and time',
                                        yaxis_title="Capacity (%)",
                                        height=int(self.height))

        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_hydro,
                          mode="lines",
                          name="Sum Hydro",
                          showlegend=True,
                          line=dict(color=self.color_hydro))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_wind,
                          mode="lines",
                          name="Sum Wind",
                          showlegend=True,
                          line=dict(color=self.color_wind))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_solar,
                          mode="lines",
                          name="Sum Solar",
                          showlegend=True,
                          line=dict(color=self.color_solar))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_nuclear,
                          mode="lines",
                          name="Sum Nuclear",
                          showlegend=True,
                          line=dict(color=self.color_nuclear))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_thermal,
                          mode="lines",
                          name="Sum Thermal",
                          showlegend=True,
                          line=dict(color=self.color_thermal))
        self.fig_load_gen.add_trace(tmp_)

        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_load,
                          mode="lines",
                          name="Total Load",
                          showlegend=True,
                          line=dict(color=self.color_load))
        self.fig_load_gen.add_trace(tmp_)

        tmp_ = go.Scatter(x=data._datetimes,
                          y=data._sum_import_export,
                          mode="lines",
                          name="Import / export",
                          showlegend=True,
                          line=dict(color=self.color_import_export))
        self.fig_load_gen.add_trace(tmp_)
        self.fig_load_gen.update_layout(title={'text': "Power production and consumption"},
                                        xaxis_title='date and time',
                                        yaxis_title="Power (MW)",
                                        height=int(self.height))

    def update_trace(self, env, tree):
        if not env.do_i_display():
            # display of the temporal figures should not be updated (for example because i run the episode until the end)
            return self.fig_load_gen, self.fig_line_cap

        data = tree.temporal_data
        beg_ = time.perf_counter()
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_hydro,
                                        selector=dict(name="Sum Hydro"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_wind,
                                        selector=dict(name="Sum Wind"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_solar,
                                        selector=dict(name="Sum Solar"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_nuclear,
                                        selector=dict(name="Sum Nuclear"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_load,
                                        selector=dict(name="Total Load"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_import_export,
                                        selector=dict(name="Import / export"))
        self.fig_load_gen.update_traces(x=data._datetimes,
                                        y=data._sum_thermal,
                                        selector=dict(name="Sum Thermal"))

        self.fig_line_cap.update_traces(x=data._datetimes,
                                        y=data._max_line_flow,
                                        selector=dict(name="Highest line capacity"))
        self.fig_line_cap.update_traces(x=data._datetimes,
                                        y=data._secondmax_line_flow,
                                        selector=dict(name="2nd highest line cap."))
        self.fig_line_cap.update_traces(x=data._datetimes,
                                        y=data._thirdmax_line_flow,
                                        selector=dict(name="3rd highest line cap."))
        self.fig_line_cap.update_traces(x=(data._datetimes[0], data._datetimes[-1]),
                                        selector=dict(name="Overflow limit"))
        self._timer_update += time.perf_counter() - beg_
        # print(f"temporal series: {self._timer_update = }")
        return self.fig_load_gen, self.fig_line_cap
