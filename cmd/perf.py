#!/usr/bin/env python3

"""
check performance values from Vsphere
"""

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection
from tools.helper import get_obj_by_name, get_metric
from pprint import pprint as pp
from tools.mon import Check, Status, Threshold

def run():
    parser = get_argparser()
    args = parser.get_args()

    if not (args.warning or args.critical):
        raise Exception("at least one of --warning or --critical is required")

    check = Check(shortname=f"PYVMOMI-PERFCOUNTER")
    check.set_threshold(
        warning=args.warning,
        critical=args.critical
    )

    args._si = service_instance.connect(args)

    try:
        vimtype = getattr(vim, args.vimtype)
    except:
        raise Exception(f"vim.{args.vimtype} is not known")

    try:
        args.perfcounter.split(":", 2)
    except:
        raise Exception("perfcounter must be composed as groupName:perfName:rollupType")

    (counter, metricId) = get_metric(args._si.content.perfManager, args.perfcounter)
    obj = get_obj_by_name(args._si, vimtype, args.vimname)

    if not metricId:
        raise Exception(f"metric not found by {args.perfcounter}")
    if not obj:
        raise Exception(f"vim.{args.vimtype} not found with name {args.vimname}")

    values = get_perf_values(args, obj, metricId)[0]

    for instance in values.value:
        if instance.id.instance == args.perfinstance:
            check.exit(
                code=check.check_threshold(instance.value[0]),
                message=f'Counter {args.perfcounter} on {args.vimtype}:{args.vimname} reported {instance.value[0]}'
            )



def get_perf_values(args, obj, metricId):
    si = args._si

    perfMgr = si.content.perfManager
#    metrics = get_key_metrics(perfMgr, group, names)

    perfQuerySpec = []
    perfQuerySpec.append(
        vim.PerformanceManager.QuerySpec(
            maxSample=1,
            entity=obj,
            metricId=[metricId],
            intervalId=args.interval,
        )
    )

    perfData = perfMgr.QueryPerf(querySpec=perfQuerySpec)
    return perfData

def get_argparser():
    parser = cli.Parser()
    #parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_required_arguments({
        'name_or_flags': ['--vimtype'],
        'options': {'action': 'store', 'help': 'the object type to check, i.e. HostSystem, Datacenter or VirtualMachine'}
    })
    parser.add_required_arguments({
        'name_or_flags': ['--vimname'],
        'options': {'action': 'store', 'help': 'name of the vimtype object'}
    })
    parser.add_required_arguments({
        'name_or_flags': ['--perfcounter'],
        'options': {'action': 'store', 'help': 'a colon separated string composed of groupInfo.key:nameInfo.key:rollupType'}
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--perfinstance'],
        'options': {
            'action': 'store',
            'default': '',
            'help': 'the instance of of the metric to monitor. defaults to empty string, '
                    'which is not always available but means an aggregated value over all instances'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--interval'],
        'options': {
            'action': 'store',
            'type': int,
            'default': 20,
            'help': 'The interval (in seconds) to aggregate over'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--critical'],
        'options': {
            'action': 'store',
            'help': 'critical threshold'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--warning'],
        'options': {
            'action': 'store',
            'help': 'warning threshold'
        }
    })
    return parser


if __name__ == "__main__":
    run()
