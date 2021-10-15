# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import setuptools
from setuptools import setup

pkgs = {
    "required": [
        "plotly",
        "dash",
        "dash_bootstrap_components",
        "grid2op>=1.6.3",
        "orjson",
        # "igraph"
        # "graphviz",
        # "networkx"
    ],
    "extras": {}
}

setup(name='grid2game',
      version='0.0.0a',
      description='A gamification of the "powergrid problem" using grid2op and dash',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Programming Language :: Python :: 3.7',
          'License :: OSI Approved :: MIT License',
          "Intended Audience :: Developers",
          "Intended Audience :: Education",
          "Intended Audience :: Science/Research",
          "Natural Language :: English"
      ],
      keywords=['powergrid', 'power-systems',
                'grid', 'grid2op',
                'Grid2Op', 'visualization'],
      author='Benjamin DONNOT',
      author_email='benjamin.donnot@rte-france.com',
      url="https://github.com/BDonnot/grid2game",
      license='MIT',
      packages=setuptools.find_packages(),
      include_package_data=True,
      install_requires=pkgs["required"],
      extras_require=pkgs["extras"],
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'grid2game=grid2game.app:start_cli'
          ]
      }
      )
