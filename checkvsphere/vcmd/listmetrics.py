#!/usr/bin/env python3

#    Copyright (C) 2023  ConSol Consulting & Solutions Software GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
print all metric counters
"""

__cmd__ = 'list-metrics'

import logging
import textwrap
from pyVmomi import vim
from ..tools import cli, service_instance

def run():
    parser = cli.Parser()
    args = parser.get_args()
    si = service_instance.connect(args)
    perfMgr = si.content.perfManager

    metrics = {}

    for counter in perfMgr.perfCounter:
        group = counter.groupInfo.key
        name = counter.nameInfo.key
        rollup = counter.rollupType
        id = counter.key

        metrics.setdefault(str(group), {}) \
            .setdefault(str(name), {}) \
            .setdefault(str(rollup), counter)

    for group in metrics:
        for name in metrics[group]:
            for rollup in metrics[group][name]:
                counter = metrics[group][name][rollup]
                print("{:4d} {}:{}:{} ({} [{}])\n{}\n".format(
                    counter.key, group, name, rollup,
                    counter.unitInfo.summary, counter.unitInfo.key,
                    textwrap.fill(
                        counter.nameInfo.summary,
                        width=72,
                        initial_indent='     ',
                        subsequent_indent='     ')
                ))


if __name__ == "__main__":
    run()
