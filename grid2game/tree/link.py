# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

from typing import Union
from grid2op.Action import BaseAction


class Link(object):
    """Link between two nodes. It stores also the "father" and the "son" of the current """
    def __init__(self,
                 action: BaseAction,
                 father: "Node"):
        self._action = action
        self._father = father
        self._son = None

    def add_son(self, son: Union["Node", None]) -> None:
        """add a son to this link"""
        self._son = son

    @property
    def action(self) -> BaseAction:
        """return the action that this link represents"""
        return self._action

    @property
    def son(self) -> Union["Node", None]:
        """return the state (as represented by a Node) after this action has been performed on the "father" state"""
        return self._son
