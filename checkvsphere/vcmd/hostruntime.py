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
check various runtime info from a host
"""

__cmd__ = 'host-runtime'

import logging
from pyVmomi import vim
from monplugin import Check, Status
from .. import CheckVsphereException
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, isbanned, isallowed, CheckArgument


def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_optional_arguments(cli.Argument.VIHOST)

    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': [
                'con',
                'health',
                'issues',
                'maintenance',
                'status',
                'temp',
                'version',
            ],
            'help': 'which runtime mode to check'
        }
    })

    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'help': 'exit with this status if the host is in maintenance, '
                    'default UNKNOWN, or CRITICAL if --mode maintenance'
        }
    })

    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of info item'))
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of info item'))

    args = parser.get_args()

    # default value differs if mode == maintenance
    if not args.maintenance_state:
        args.maintenance_state = 'CRITICAL' if args.mode == 'maintenance' else 'UNKNOWN'

    si = service_instance.connect(args)

    check = Check()

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    try:
        vm = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve=({'name': args.vihost} if args.vihost else None),
            properties=['name', 'runtime.inMaintenanceMode'],
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"host {args.vihost or ''} not found")

    result = []

    if vm['props']['runtime.inMaintenanceMode']:
        check.exit(
            Status[args.maintenance_state],
            f"host {vm['props']['name']} is in maintenance"
        )

    okmessage = "No errors"

    if args.mode == "health":
        okmessage = check_health(check, vm, args, result)
    elif args.mode == "status":
        check_status(check, vm, args, result)
    elif args.mode == "con":
        check_con(check, vm, args, result)
    elif args.mode == "temp":
        okmessage = check_temp(check, vm, args, result)
    elif args.mode == "issues":
        okmessage = check_issues(check, vm, args, result)
    elif args.mode == "version":
        version = vm['obj'].obj.summary.config.product.fullName
        check.exit(Status.OK, version)
    elif args.mode == 'maintenance':
        check.exit(Status.OK, "Host is not in maintenance")

    opts = {}
    if not args.verbose:
        opts['allok'] = okmessage

    (code, message) = check.check_messages(separator="\n", separator_all='\n', **opts)
    check.exit(
        code=code,
        message=( message or  "everything ok" )
    )

def format_issue(issue):
    things = [
        # checkfor, name, how to get value
        ('datacenter', lambda x: 'Datacenter: ' + x.datacenter.name),
        ('host', lambda x: 'Host: ' + x.host.name),
        ('vm', lambda x: 'VM: ' + x.vm.name),
        ('computeResource', lambda x: 'Compute Resource: ' + x.computeResource.name),
        ('dvs', lambda x: 'Virtual Switch: ' + x.dvs.name),
        ('ds', lambda x: 'Datastore: ' + x.ds.name),
        ('net', lambda x: 'Network: ' + x.net.name),
        (None, lambda x: 'Message: ' + x.fullFormattedMessage),
        ('userName', lambda x: f'(caused by {x.userName})' if x.userName != "" else None),
    ]

    formattedThings = []
    for thing in things:
        if thing[0]:
            if not ( getattr(issue, thing[0], None) and getattr(issue, thing[0]) ):
                continue

        formattedThing = thing[1](issue)
        if formattedThing:
            formattedThings.append( formattedThing )

    return ", ".join(formattedThings)


def check_issues(check, vm, args, result):
    issues = vm['obj'].obj.configIssue
    for issue in issues:
        if isbanned(args, issue.fullFormattedMessage):
            continue
        if not isallowed(args, issue.fullFormattedMessage):
            continue
        check.add_message(Status.CRITICAL, format_issue(issue))

    return "No issues found"


def check_con(check, vm, args, result):
    con = vm['obj'].obj.runtime.connectionState
    status = Status.OK
    if con == "disconnected":
        status = Status.WARNING
    elif con == "notResponding":
        status = Status.CRITICAL
    check.exit(
        status,
        message = f"connection state is '{con}'"
    )

def check_status(check, vm, args, result):
    color = vm['obj'].obj.overallStatus
    status = health2state(color)
    check.exit(status, f"overall status is {str(color).upper()}")

def check_temp(check, vm, args, result):
    systemRuntime = vm['obj'].obj.runtime.healthSystemRuntime
    if not systemRuntime:
        check.exit(
            Status.UNKNOWN,
            "Temperature status unavailable"
        )

    numericinfo = systemRuntime.systemHealthInfo.numericSensorInfo
    for info in numericinfo:
        if info.sensorType != "temperature":
            continue
        if isbanned(args, info.name):
            continue
        if not isallowed(args, info.name):
            continue
        state = health2state(info.healthState.key)
        name = info.name.rstrip(' Temp')
        check.add_perfdata(label=name, value=info.currentReading * (10 ** info.unitModifier))
        check.add_message(state, f"{name} is {info.healthState.key}")

    return "All temperature sensors green"

def check_health(check, vm, args, result):
    healthsystem = vm['obj'].obj.runtime.healthSystemRuntime
    if not healthsystem:
        check.exit(
            Status.UNKNOWN,
            "system health status not available, "
            "no vim.Host.runtime.healthSystemRuntime found"
        )
    if not healthsystem.hardwareStatusInfo:
        check.exit(
            Status.UNKNOWN,
            "hardware health information not available, "
            "no vim.Host.runtime.healthSystemRuntime.hardwareStatusInfo found"
        )

    filterunknown = lambda x: x.status.key != "unknown"
    cpustatus = healthsystem.hardwareStatusInfo.cpuStatusInfo
    storagestatus = list(filter(filterunknown, healthsystem.hardwareStatusInfo.storageStatusInfo))
    memorystatus = list(filter(filterunknown, healthsystem.hardwareStatusInfo.memoryStatusInfo))
    numericsensor = healthsystem.systemHealthInfo.numericSensorInfo

    count = {}

    # "[$status2text{$fstate}] [Type: $type] [Name: $item_ref->{name}] [Label: $item_ref->{label}] [Summary: $item_ref->{summary}]$multiline";
    if memorystatus:
        for info in memorystatus:
            state = health2state(info.status.key)
            if isbanned(args, info.name):
                continue
            if not isallowed(args, info.name):
                continue
            if state == Status.UNKNOWN:
                continue
            check.add_message(state, f"{state.name} [Type: Memory] [Name: { info.name }] [Summary: { info.status.summary }]")
            count.setdefault('memory', 0)
            count['memory'] += 1

    if cpustatus:
        for info in cpustatus:
            state = health2state(info.status.key)
            if state == Status.UNKNOWN:
                # I don't know if this is true, check_vmware_esx said that
                check.exit(Status.CRITICAL,
                    "No result from CIM server regarding health state. "
                    "CIM server is probably not running or not running correctly! "
                    "Please restart!"
                )
            check.add_message(state, f"{state.name} [Type: CPU] [Name: { info.name }] [Summary: { info.status.summary }]")
            count.setdefault('cpu', 0)
            count['cpu'] += 1

    if storagestatus:
        for info in storagestatus:
            if isbanned(args, info.name):
                continue
            if not isallowed(args, info.name):
                continue
            state = health2state(info.status.key)
            if state == Status.UNKNOWN:
                continue

            check.add_message(state, f"{state.name} [Type: Storage] [Name: { info.name }] [Summary: { info.status.summary }]")
            count.setdefault('storage', 0)
            count['storage'] += 1


    if numericsensor:
        for info in numericsensor:
            if info.sensorType == "Software Components":
                # It is said they make no sense
                continue
            if isbanned(args, info.name):
                continue
            if not isallowed(args, info.name):
                continue
            if 'unknown' in info.healthState.label and 'Cannot report' in info.healthState.summary:
                # Filter out sensors which have no valid data. Often a sensor is recognized by vmware
                # but has not the ability to report something senseful. So it can be skipped.
                continue

            state = health2state(info.healthState.key)
            if state == Status.UNKNOWN:
                continue

            check.add_message(state,
                f"{state.name} [Type: {info.sensorType}] "
                f"[Name: {info.name}] [Label: {info.healthState.label}] "
                f"[Summary: {info.healthState.summary}]"
            )
            count.setdefault(str(info.sensorType), 0)
            count[str(info.sensorType)] += 1

    okmessage = (
        f"All {sum(count.values())} health checks are GREEN: " +
        (', '.join(list( f"{x}: {count[x]}" for x in count )))
    )
    return okmessage

def health2state(color):
    return {
        "green": Status.OK,
        "yellow": Status.WARNING,
        "red": Status.CRITICAL,
    }.get(color.lower(), Status.UNKNOWN)

if __name__ == "__main__":
    run()
