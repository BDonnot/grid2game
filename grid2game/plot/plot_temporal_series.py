# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import plotly.colors as pc
import plotly.graph_objects as go

from grid2op.PlotGrid.config import NUKE_COLOR, THERMAL_COLOR, WIND_COLOR, SOLAR_COLOR, HYDRO_COLOR

from grid2game.plot.plot_param import PlotParams


class PlotTemporalSeries(PlotParams):
    def __init__(self, env):
        super().__init__()

        # maybe in the parameters
        self.color_nuclear = NUKE_COLOR
        self.color_thermal = THERMAL_COLOR
        self.color_wind = WIND_COLOR
        self.color_solar = SOLAR_COLOR
        self.color_hydro = HYDRO_COLOR
        self.color_load = "black"

        self.env = env

        self.fig_load_gen = None
        self.fig_line_cap = None
        self.init_figures()

    def init_figures(self):
        self.fig_load_gen = go.Figure()
        self.fig_line_cap = go.Figure()

        self.init_traces()
        # self.fig_load_gen.update_layout(clickmode='event+select')
        # self.fig_line_cap.update_layout(clickmode='event+select')

    def init_traces(self):
        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._max_line_flow,
                          mode="lines",
                          name="Max. Line capacity",
                          hoverinfo='skip',
                          showlegend=True)
        self.fig_line_cap.add_trace(tmp_)
        tmp_ = go.Scatter(x=(self.env._datetimes[0],self.env._datetimes[-1]),
                          y=(1., 1.),
                          mode="lines",
                          name="Overflow limit",
                          hoverinfo='skip',
                          showlegend=True,
                          line=dict(color="red", dash="dash"))
        self.fig_line_cap.add_trace(tmp_)
        self.fig_line_cap.update_layout(title={'text': "Line capacity"},
                                        xaxis_title='date and time',
                                        yaxis_title="Capacity (%)")

        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_hydro,
                          mode="lines",
                          name="Sum Hydro",
                          showlegend=True,
                          line=dict(color=self.color_hydro))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_wind,
                          mode="lines",
                          name="Sum Wind",
                          showlegend=True,
                          line=dict(color=self.color_wind))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_solar,
                          mode="lines",
                          name="Sum Solar",
                          showlegend=True,
                          line=dict(color=self.color_solar))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_nuclear,
                          mode="lines",
                          name="Sum Nuclear",
                          showlegend=True,
                          line=dict(color=self.color_nuclear))
        self.fig_load_gen.add_trace(tmp_)
        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_thermal,
                          mode="lines",
                          name="Sum Thermal",
                          showlegend=True,
                          line=dict(color=self.color_thermal))
        self.fig_load_gen.add_trace(tmp_)

        tmp_ = go.Scatter(x=self.env._datetimes,
                          y=self.env._sum_load,
                          mode="lines",
                          name="Sum Load",
                          showlegend=True,
                          line=dict(color=self.color_load))
        self.fig_load_gen.add_trace(tmp_)
        self.fig_load_gen.update_layout(title={'text': "Power production and consumption"},
                                        xaxis_title='date and time',
                                        yaxis_title="Power (MW)")

    def update_trace(self):
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_hydro,
                                        selector=dict(name="Sum Hydro"))
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_wind,
                                        selector=dict(name="Sum Wind"))
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_solar,
                                        selector=dict(name="Sum Solar"))
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_nuclear,
                                        selector=dict(name="Sum Nuclear"))
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_load,
                                        selector=dict(name="Sum Load"))
        self.fig_load_gen.update_traces(x=self.env._datetimes,
                                        y=self.env._sum_thermal,
                                        selector=dict(name="Sum Thermal"))

        self.fig_line_cap.update_traces(x=self.env._datetimes,
                                        y=self.env._max_line_flow,
                                        selector=dict(name="Max. Line capacity"))
        self.fig_line_cap.update_traces(x=(self.env._datetimes[0], self.env._datetimes[-1]),
                                        selector=dict(name="Overflow limit"))