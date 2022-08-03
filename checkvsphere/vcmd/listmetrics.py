#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'list-metrics'

import logging
import textwrap
from pyVmomi import vim
from ..tools import cli, service_instance
from pprint import pprint as pp

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
