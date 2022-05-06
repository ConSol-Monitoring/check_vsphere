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

    check = Check(shortname="VSPHERE-PERFCOUNTER")
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

    (counter, metricId) = get_metric(args._si.content.perfManager, args.perfcounter, args.perfinstance)

    # I hate you so much vmware
    # https://vdc-download.vmware.com/vmwb-repository/dcr-public/bf660c0a-f060-46e8-a94d-4b5e6ffc77ad/208bc706-e281-49b6-a0ce-b402ec19ef82/SDK/vsphere-ws/docs/ReferenceGuide/cpu_counters.html
    if counter.unitInfo.key == 'percent':
        factor = 0.01
    else:
        factor = 1

    obj = get_obj_by_name(args._si, vimtype, args.vimname)

    if not metricId:
        raise Exception(f"metric not found by {args.perfcounter}:{args.perfinstance}, "
                        "maybe --perfinstance='*' helps to examine the available instances")
    if not obj:
        raise Exception(f"vim.{args.vimtype} not found with name {args.vimname}")

    try:
        values = get_perf_values(args, obj, metricId)[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"Cannot find {args.perfcounter} for the queried resources")

    if args.perfinstance == '':
        for instance in values.value:
            val = instance.value[0] * factor
            if instance.id.instance == args.perfinstance:
                check.add_perfdata(
                    label = args.perfcounter,
                    value = val,
                    threshold = check.threshold,
                )
                check.exit(
                    code=check.check_threshold(val),
                    message=f'Counter {args.perfcounter} on {args.vimtype}:{args.vimname} reported {val}'
                )
    else:
        for instance in values.value:
            if instance.id.instance == '':
                # ignore the aggregate if we query a specific or all instances
                continue
            if args.perfinstance == '*' or args.perfinstance == instance.id.instance:
                val = instance.value[0] * factor
                check.add_perfdata(
                    label = f'{args.perfcounter}_{instance.id.instance}',
                    value = val,
                    threshold = check.threshold,
                )
                check.add_message(
                    check.threshold.get_status(val),
                    f"{args.perfcounter}_{instance.id.instance} has value {val}"
                )

        (code, message) = check.check_messages(separator='\n  ')
        check.exit(
            code=code,
            message=message
        )

        raise NotImplementedError("only perfinstance '' is currently supported")



def get_perf_values(args, obj, metricId):
    si = args._si

    perfMgr = si.content.perfManager

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
    try:
        run()
    except SystemExit as e:
        if e.code > 3 or e.code < 0:
            print("UNKNOWN EXIT CODE")
            raise SystemExit(Status.UNKNOWN)
    except Exception as e:
        print("UNKNOWN - " + str(e))
        raise SystemExit(Status.UNKNOWN)
