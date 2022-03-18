#!/usr/bin/env python3

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from tools.helper import generic_performance_values
from http.client import HTTPConnection
from tools.helper import get_obj_by_name
from pprint import pprint as pp

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
        key = 'read.average:*'
        valobj = values[0].get(key, None)
        if valobj:
            value = 0
            try:
                value = valobj.value[0]
            except: pass
            print(f"OK - I/O read={ value } kB.")
            print(f"|io_read={value}kB;")
        else:
            raise Exception("no counter found")
    elif args.subselect == "read_latency":
        key = 'totalReadLatency.average:*'
        valobj = values[0].get(key, None)
        if valobj:
            value = 0
            try:
                value = valobj.value[0]
            except: pass
            print(f"OK - I/O read_latency={ value } ms.")
            print(f"|io_read_latency={ value }ms;")
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
