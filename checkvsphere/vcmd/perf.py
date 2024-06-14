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
check performance values from Vsphere
"""

__cmd__ = 'perf'

import logging
from pyVmomi import vim
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, get_metric, CheckArgument
from monplugin import Check, Status, Threshold

'''
[kiloBytes]
[megaBytes]
[teraBytes]
[percent]
[microsecond]
[millisecond]
[second]
[celsius]
[joule]
[kiloBytesPerSecond]
[megaHertz]
[number]
[watt]
'''


def get_counter_info(counter):
    info = {}
    info['factor'] = 1
    info['unit'] = counter.unitInfo.summary
    info['perfUnit'] = None
    unit = counter.unitInfo.key
    if unit == 'percent':
        # percent is actually ‱ (permyriad)
        info['factor'] = 0.01
        info['unit'] = '%'
        info['perfUnit'] = '%'
    elif unit.endswith('Bytes'):
        unit = unit.capitalize()
        info['perfUnit'] = unit[0] + 'B'
        info['unit'] = info['perfUnit'] + 'ytes'
    elif unit.endswith('second'):
        if unit.startswith('milli'):
            info['perfUnit'] = 'ms'
        elif unit.startswith('micro'):
            info['perfUnit'] = 'us'
        elif unit == 'second':
            info['perfUnit'] = 's'
    elif unit.endswith('number'):
        info['unit'] = ''

    return info


def run():
    parser = get_argparser()
    args = parser.get_args()

    check = Check()
    check.set_threshold(warning=args.warning, critical=args.critical)

    args._si = service_instance.connect(args)

    try:
        vimtype = getattr(vim, args.vimtype)
    except:
        raise Exception(f"vim.{args.vimtype} is not known")

    try:
        args.perfcounter.split(":", 2)
    except:
        raise Exception("perfcounter must be composed as groupName:perfName:rollupType")

    (counter, metricId) = get_metric(
        args._si.content.perfManager, args.perfcounter, args.perfinstance
    )

    # I hate you so much vmware
    # https://vdc-download.vmware.com/vmwb-repository/dcr-public/bf660c0a-f060-46e8-a94d-4b5e6ffc77ad/208bc706-e281-49b6-a0ce-b402ec19ef82/SDK/vsphere-ws/docs/ReferenceGuide/cpu_counters.html

    vms = find_entity_views(
        args._si,
        vimtype,
        properties=['name'],
        begin_entity=args._si.content.rootFolder,
        sieve=( {'name': args.vimname} if args.vimname else None )
    )

    try:
        obj = vms[0]['obj'].obj
        props = vms[0]['props']
    except IndexError:
        check.exit(Status.UNKNOWN, f"{args.vimtype} {args.vimname or ''} not found")

    if not metricId:
        raise Exception(
            f"metric not found by {args.perfcounter}:{args.perfinstance}, "
            "maybe --perfinstance='*' helps to examine the available instances"
        )
    if not obj:
        raise Exception(f"vim.{args.vimtype} not found with name {args.vimname}")

    if 'runtime.inMaintenanceMode' in props:
        if props['runtime.inMaintenanceMode']:
            check.exit(
                Status[args.maintenance_state],
                f"{args.vimname or props['name']} is in maintenance"
            )

    counterInfo = get_counter_info(counter)

    try:
        values = get_perf_values(args, obj, metricId)[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"Cannot find {args.perfcounter} for the queried resources")

    if not values.value:
        check.exit(code=Status.UNKNOWN, message="No data returned")

    if args.perfinstance == '':
        for instance in values.value:
            val = instance.value[0] * counterInfo['factor']
            if instance.id.instance == args.perfinstance:
                check.add_perfdata(
                    label=args.perfcounter,
                    value=val,
                    threshold=check.threshold,
                    uom=counterInfo['perfUnit'],
                )
                check.exit(
                    code=check.check_threshold(val),
                    message=f'Counter {args.perfcounter} on {args.vimtype}:{args.vimname or props["name"]} reported {val:.8g} {counterInfo["unit"]}',
                )
    else:
        for instance in values.value:
            if instance.id.instance == '':
                # ignore the aggregate if we query a specific or all instances
                continue
            if args.perfinstance == '*' or args.perfinstance == instance.id.instance:
                val = instance.value[0] * counterInfo['factor']
                check.add_perfdata(
                    label=f'{instance.id.instance} {args.perfcounter}',
                    value=val,
                    threshold=check.threshold,
                    uom=counterInfo['perfUnit'],
                )
                check.add_message(
                    check.threshold.get_status(val),
                    f"'{instance.id.instance} {args.perfcounter}' has value {val:.8g} {counterInfo['unit']}",
                )

        (code, message) = check.check_messages(separator='\n  ')
        check.exit(code=code, message=message)


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

    parser.add_optional_arguments( CheckArgument.CRITICAL_THRESHOLD )
    parser.add_optional_arguments( CheckArgument.WARNING_THRESHOLD )
    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'default': 'UNKNOWN',
            'help': 'exit with this status if the host is in maintenance, only does something with --vimtype HostSystem'
        }
    })

    parser.add_required_arguments( CheckArgument.VIMTYPE )
    parser.add_optional_arguments( CheckArgument.VIMNAME )

    parser.add_required_arguments(
        {
            'name_or_flags': ['--perfcounter'],
            'options': {
                'action': 'store',
                'help': 'a colon separated string composed of groupInfo.key:nameInfo.key:rollupType',
            },
        }
    )

    parser.add_optional_arguments(
        {
            'name_or_flags': ['--perfinstance'],
            'options': {
                'action': 'store',
                'default': '',
                'help': 'the instance of of the metric to monitor. defaults to empty string, '
                'which is not always available but means an aggregated value over all instances',
            },
        }
    )
    parser.add_optional_arguments(
        {
            'name_or_flags': ['--interval'],
            'options': {
                'action': 'store',
                'type': int,
                'default': 20,
                'help': 'The interval (in seconds) to aggregate over',
            },
        }
    )

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
