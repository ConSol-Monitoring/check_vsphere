#!/usr/bin/env python3

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection
from tools.helper import get_obj_by_name
import re

#sub return_host_performance_values
#    {
#    my $values;
#    my $host_name = shift(@_);
#    my $maintenance_mode_state = shift(@_);
#    my $host_view;
#
#    $host_view = Vim::find_entity_views(view_type => 'HostSystem', filter => $host_name, properties => (['name', 'runtime.inMaintenanceMode']) ); # Added properties named argument.

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

def generic_performance_values(si, objs, group, names):
    perfMgr = si.content.perfManager
    counters = get_key_metrics(perfMgr, group, names)
    print(counters)

def check_host_io(args):
    hostname = args.vihost
    host = get_obj_by_name(args._si, vim.HostSystem, args.vihost)

    generic_performance_values(args._si, host, 'disk', [
        'busResets.summation:*',
        'commandsAborted.summation:*',
        'deviceLatency.average:*',
        'kernelLatency.average:*',
        'queueLatency.average:*',
        'read.average:*',
        'totalLatency.average:*'
        'totalReadLatency.average:*',
        'totalWriteLatency.average:*',
        'usage.average:*',
        'write.average:*',
    ])

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
