#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'host-runtime'

import logging
from ..tools.helper import find_entity_views
from pyVmomi import vim
from pyVim.task import WaitForTask
from ..tools import cli, service_instance
from monplugin import Check, Status
from http.client import HTTPConnection
from .. import CheckVsphereException


def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_required_arguments(cli.Argument.VIHOST)

    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': [
                'health',
                'status',
                'con',
            ],
            'help': 'which runtime mode to check'
        }
    })

    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'default': 'UNKNOWN',
            'help': 'exit with this status if the host is in maintenance, only does something with --vimtype HostSystem'
        }
    })


    args = parser.get_args()
    si = service_instance.connect(args)

    check = Check(shortname='VSPHERE-RUNTIME')

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    try:
        vm = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve={'name': args.vihost},
            properties=['name', 'runtime', 'overallStatus', 'configIssue', 'summary.config']
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"host {args.vihost} not found")

    result = []

    if vm['props']['runtime'].inMaintenanceMode:
        status = getattr(Status, args.maintenance_state)
        check.exit(
            status,
            f"host {args.vihost} is in maintenance mode, check skipped"
        )

    if args.mode == "health":
        check_health(check, vm, args, result)
    elif args.mode == "status":
        check_status(check, vm, args, result)
    elif args.mode == "con":
        check_con(check, vm, args, result)

    (code, message) = check.check_messages(separator="\n", separator_all='\n', allok='All sensors ok')
    check.exit(
        code=code,
        message=( message or  "everything ok" )
    )

def check_con(check, vm, args, result):
    con = vm['props']['runtime'].connectionState
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
    color = vm['props']['overallStatus']
    status = health2state(color)
    check.exit(status, f"overall status is {str(color).upper}")

def check_health(check, vm, args, result):
    runtime = vm['props']['runtime']
    healthsystem = runtime.healthSystemRuntime
    filterunknown = lambda x: x.status.key != "unknown"
    cpustatus = healthsystem.hardwareStatusInfo.cpuStatusInfo
    storagestatus = list(filter(filterunknown, healthsystem.hardwareStatusInfo.storageStatusInfo))
    memorystatus = list(filter(filterunknown, healthsystem.hardwareStatusInfo.memoryStatusInfo))
    numericsensor = healthsystem.systemHealthInfo.numericSensorInfo

    # "[$status2text{$fstate}] [Type: $type] [Name: $item_ref->{name}] [Label: $item_ref->{label}] [Summary: $item_ref->{summary}]$multiline";
    if memorystatus:
        for info in memorystatus:
            state = health2state(info.status.key)
            #print((state, f"{state.name} [Type: Memory] [Name: { info.name }] [Summary: { info.status.summary }]"))
            check.add_message(state, f"{state.name} [Type: Memory] [Name: { info.name }] [Summary: { info.status.summary }]")

    if cpustatus:
        for info in cpustatus:
            state = health2state(info.status.key)
            if state == Status.UNKNOWN:
                # I don't know if this is true
                check.exit(Status.CRITICAL,
                    "No result from CIM server regarding health state. "
                    "CIM server is probably not running or not running correctly! "
                    "Please restart!"
                )
            check.add_message(state, f"{state.name} [Type: CPU] [Name: { info.name }] [Summary: { info.status.summary }]")

    if storagestatus:
        for info in storagestatus:
            state = health2state(info.status.key)
            #print(info)
            #print((state, f"{state.name} [Type: Memory] [Name: { info.name }] [Summary: { info.status.summary }]"))
            check.add_message(state, f"{state.name} [Type: Memory] [Name: { info.name }] [Summary: { info.status.summary }]")


    if numericsensor:
        for info in numericsensor:
            if info.sensorType == "Software Components":
                # It is said they make no sense
                continue
            if 'unknown' in info.healthState.label and 'Cannot report' in info.healthState.summary:
                # Filter out sensors which have not valid data. Often a sensor is recognized by vmware
                # but has not the ability to report something senseful. So it can be skipped.
                continue

            state = health2state(info.healthState.key)
            check.add_message(state,
                f"{state.name} [Type: {info.sensorType}] "
                f"[Name: {info.name}] [Label: {info.healthState.label}] "
                f"[Summary: {info.healthState.summary}]"
            )


def health2state(color):
    return {
        "green": Status.OK,
        "yellow": Status.WARNING,
        "red": Status.CRITICAL,
    }.get(color.lower(), Status.UNKNOWN)

if __name__ == "__main__":
    run()