#!/usr/bin/env python3

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection
from tools.helper import get_obj_by_name
import re


def get_key_metrics(perfMgr, group, names):
    counters = []
    for counter in perfMgr.perfCounter:
        if counter.groupInfo.key == group:
            cur_name = f'{counter.nameInfo.key}.{counter.rollupType}'
            for n in names:
                if re.match(n, cur_name):
                    match = re.match(r'(\w+)\.(\w+):*(.*)', n)
                    counters.append(vim.PerformanceManager.MetricId(
                        counterId = counter.key,
                        instance = match.groups()[2]
                    ))
    return counters

def generic_performance_values(si, views, group, names):
    perfMgr = si.content.perfManager
    metrics = get_key_metrics(perfMgr, group, names)

    perfQuerySpec = []
    for v in views:
        perfQuerySpec.append(
            vim.PerformanceManager.QuerySpec(
                maxSample=1,
                entity=v,
                metricId=metrics,
                intervalId=20,
            )
        )

    perfData = perfMgr.QueryPerf(querySpec=perfQuerySpec)

    values = []
    for p in perfData:
        unsorted = p.value # is it really unsorted? doesn't seem so ...

        # check if the order matches the order of the query
        for m, p in zip(metrics, unsorted):
            if not m or not p or p.id.counterId != m.counterId:
                raise Exception("FIXME: unsorted is really unsorted...")

        values.append(unsorted)

    return values



def check_host_io(args):
    hostname = args.vihost
    host = get_obj_by_name(args._si, vim.HostSystem, args.vihost)
    # TODO take care about maintenance mode on host
    values = generic_performance_values(args._si, [host], 'disk', [
        'busResets.summation:*',
        'commandsAborted.summation:*',
        'deviceLatency.average:*',
        'deviceLatency.verage:*',
        'kernelLatency.average:*',
        'queueLatency.average:*',
        'read.average:*',
        'totalLatency.average:*'
        'totalReadLatency.average:*',
        'totalWriteLatency.average:*',
        'usage.average:*',
        'write.average:*',
    ])

    print(values)

def run():
    parser = cli.Parser()
    #parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments(cli.Argument.VM_NAME)
    parser.add_optional_arguments(cli.Argument.CLUSTER_NAME)
    parser.add_required_arguments({
        'name_or_flags': ['--subselect'],
        'options': {'action': 'store', 'help': 'read/write/...'}
    })

    args = parser.get_args()
    # print(args)

    if not ( args.vm_name or args.vihost or args.cluster_name ):
        raise Exception("one of --cluster-name, --vihost or --vm-name is required")

    args._si = service_instance.connect(args)

    if args.vm_name:
        check_vm_io(args)
    elif args.vihost:
        check_host_io(args)
    elif args.cluster_name:
        check_cluster_io(args)

if __name__ == "__main__":
    run()
