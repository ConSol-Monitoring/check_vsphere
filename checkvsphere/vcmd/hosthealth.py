#!/usr/bin/env python3

"""
--select runtime --subselect health
"""

__cmd__ = None # not finished yet 'host-health'

import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from http.client import HTTPConnection
from ..tools import cli, service_instance
from ..tools.helper import get_obj_by_name, get_metric, CheckArgument
from ..tools.helper import find_entity_views, get_obj_by_name, get_metric
from monplugin import Check, Status, Threshold

def health_status(color):
    return {
        'red': Status.CRITICAL,
        'yellow': Status.WARNING,
        'green': Status.OK
    }.get(color.lower(), Status.UNKNOWN)


def run():
    parser = get_argparser()
    args = parser.get_args()

    check = Check(shortname="VSPHERE-HOSTHEALTH")

    args._si = service_instance.connect(args)

    vms = find_entity_views(
        args._si,
        vim.HostSystem,
        begin_entity=args._si.content.rootFolder,
        sieve={'name': args.vihost},
        properties=['runtime', 'overallStatus', 'configIssue', 'summary.config.product.fullName']
    )

    try:
        obj = vms[0]['obj'].obj
        props = vms[0]['props']
    except IndexError:
        check.exit(Status.UNKNOWN, f"{args.vimtype} {args.vimname} not found")

    if 'runtime.inMaintenanceMode' in props:
        status = getattr(Status, args.maintenance_state)
        if props['runtime.inMaintenanceMode']:
            check.exit(status, f"{args.vimname} is in maintenance")

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
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'default': 'UNKNOWN',
            'help': 'exit with this status if the host is in maintenance, only does something with --vimtype HostSystem'
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
