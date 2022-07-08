# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.
import time
from abc import ABC, abstractmethod


class ComputeWrapper(ABC):
    """simple class to wrapper the logic of an heavy computation going on.

     For the computation itself, please override `do_computation`
     """
    def __init__(self):
        self.__is_computing = False  # whether or not something is being computed
        self.__computation_started = False  # whether or not something needs to be computed
        self.__is_computing_recommandations = False # whether or not variant trees are being computed
        self.count = 0

    @abstractmethod
    def do_computation(self):
        pass

    def heavy_compute(self):
        if not self.__computation_started:
            return None
        if self.__is_computing:
            return None
        self.__is_computing = True
        res = self.do_computation()
        self.__is_computing = False
        return res

    def is_computing_recommandations(self):
        return self.__is_computing_recommandations

    def start_recommandations_computation(self):
        self.__is_computing_recommandations = True

    def stop_recommandations_computation(self):
        self.__is_computing_recommandations = False

    def is_computing(self):
        return self.__is_computing

    def start_computation(self):
        self.__computation_started = True

    def stop_computation(self):
        self.__computation_started = False

    def needs_compute(self):
        return self.__computation_started
