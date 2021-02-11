# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.


import plotly.colors as pc


class PlotParams(object):
    """this is what you need to modify if you want to customize the plots"""
    def __init__(self):
        # figure width
        # self.width = 1280  # original
        # self.height = 720  # original
        ratio = 1
        self.width = 1280 / ratio
        self.height = 720 / ratio

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

    def _set_layout(self, fig):
        """set the layout of the figure, for now called only once"""
        # see https://dash.plotly.com/interactive-graphing
        fig.update_layout(# width=self.width,
                          # height=self.height,
                          xaxis=dict(visible=False),
                          yaxis=dict(visible=False),
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=0, r=0, b=0, t=0, pad=0),
                          clickmode='event+select'
                          )
        # fig.update_yaxes(automargin=True)
        # fig.update_xaxes(automargin=True)