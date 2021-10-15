# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import copy
import numpy as np
from typing import Union

from grid2op.Observation import BaseObservation


class TemporalNodeData(object):
    """
    This class represents the temporal data at each node of the graph.
    It is used to plot some temporal information on the UI
    """
    def __init__(self,
                 current_obs: Union[None, BaseObservation],
                 father_node_data: "TemporalNodeData"):
        if father_node_data is not None:
            # I am not the root of the tree
            self._sum_load = copy.deepcopy(father_node_data._sum_load)
            self._max_line_flow = copy.deepcopy(father_node_data._max_line_flow)
            self._secondmax_line_flow = copy.deepcopy(father_node_data._secondmax_line_flow)
            self._thirdmax_line_flow = copy.deepcopy(father_node_data._thirdmax_line_flow)
            self._sum_solar = copy.deepcopy(father_node_data._sum_solar)
            self._sum_wind = copy.deepcopy(father_node_data._sum_wind)
            self._sum_thermal = copy.deepcopy(father_node_data._sum_thermal)
            self._sum_hydro = copy.deepcopy(father_node_data._sum_hydro)
            self._sum_nuclear = copy.deepcopy(father_node_data._sum_nuclear)
            self._datetimes = copy.deepcopy(father_node_data._datetimes)
        else:
            # I am data at the root of the tree
            self._sum_load = []
            self._max_line_flow = []
            self._secondmax_line_flow = []
            self._thirdmax_line_flow = []
            self._sum_solar = []
            self._sum_wind = []
            self._sum_thermal = []
            self._sum_hydro = []
            self._sum_nuclear = []
            self._datetimes = []
            
        self._fill_info_vect(current_obs)

    def _fill_info_vect(self, current_obs):
        self._sum_load.append(np.sum(current_obs.load_p))
        rhos_ = np.partition(current_obs.rho.flatten(), -3)
        self._max_line_flow.append(rhos_[-1])
        self._secondmax_line_flow.append(rhos_[-2])
        self._thirdmax_line_flow.append(rhos_[-3])
        if hasattr(current_obs, "gen_p"):
            vect_ = current_obs.gen_p
        else:
            vect_ = current_obs.prod_p
            import warnings
            warnings.warn("DEPRECATED: please use grid2op >= 1.5 for benefiting from all grid2game feature",
                          DeprecationWarning)
        self._sum_solar.append(np.sum(vect_[current_obs.gen_type == "solar"]))
        self._sum_wind.append(np.sum(vect_[current_obs.gen_type == "wind"]))
        self._sum_thermal.append(np.sum(vect_[current_obs.gen_type == "thermal"]))
        self._sum_hydro.append(np.sum(vect_[current_obs.gen_type == "hydro"]))
        self._sum_nuclear.append(np.sum(vect_[current_obs.gen_type == "nuclear"]))
        self._datetimes.append(current_obs.get_time_stamp())
