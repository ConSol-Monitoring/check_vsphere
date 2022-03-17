#!/usr/bin/env python3

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection
from tools.helper import get_obj_by_name
import re
from pprint import pprint as pp


def get_key_metrics(perfMgr, group, names):
    metrics = {}
    for counter in perfMgr.perfCounter:
        if counter.groupInfo.key == group:
            cur_name = f'{counter.nameInfo.key}.{counter.rollupType}'
            for n in names:
                if n.startswith(cur_name):
                    match = re.match(r'^(\w+)\.(\w+):(.*)', n)
                    metrics[counter.key] = (
                        n,
                        vim.PerformanceManager.MetricId(
                            counterId = counter.key,
                            instance = match.groups()[2]
                        )
                    )
    return metrics

def generic_performance_values(si, views, group, names):
    perfMgr = si.content.perfManager
    metrics = get_key_metrics(perfMgr, group, names)
    perfQuerySpec = []

    for v in views:
        perfQuerySpec.append(
            vim.PerformanceManager.QuerySpec(
                maxSample=1,
                entity=v,
                metricId=[ x[1] for x in metrics.values() ],
                intervalId=20,
            )
        )

    perfData = perfMgr.QueryPerf(querySpec=perfQuerySpec)

    values = []

    for p in perfData:
        vals = {}
        for n in names:
            vals[n] = None
        for v in p.value:
            vals[metrics[v.id.counterId][0]] = v
        values.append(vals)

    return values



def check_host_io(args):
    hostname = args.vihost
    host = get_obj_by_name(args._si, vim.HostSystem, args.vihost)
    if not host:
        raise Exception(f"host {args.vihost} not found")

    # TODO take care about maintenance mode on host
    values = generic_performance_values(args._si, [host], 'disk', [
        'a.b:*',
        'busResets.summation:*',
        'commandsAborted.summation:*',
        'deviceLatency.average:*',
        'deviceLatency.verage:*',
        'kernelLatency.average:*',
        'queueLatency.average:*',
        'read.average:*',
        'totalLatency.average:*',
        'totalReadLatency.average:*',
        'totalWriteLatency.average:*',
        'usage.average:*',
        'write.average:*',
    ])

    if args.subselect == "read":
        key = 'busResets.summation:*'
        valobj = values[0].get(key, None)
        if valobj:
            value = 0
            try:
                value = valobj.value[0]
            except: pass
            print(f"OK - I/O read={ value } KB/sec.")
            print(f"|io_read={value}KB;")
        else:
            raise Exception("no counter found")

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
