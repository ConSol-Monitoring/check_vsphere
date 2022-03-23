#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection
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
                print("{} {} {} {}\n  {}".format(
                    counter.key, group, name, rollup,
                    counter.nameInfo.summary
                ))

if __name__ == "__main__":
    run()
