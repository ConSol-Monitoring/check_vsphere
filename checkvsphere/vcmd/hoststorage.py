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
checks storage adapters
"""

__cmd__ = 'host-storage'

import re
from pyVmomi import vim, vmodl
from monplugin import Check, Status, Threshold, Range
from ..tools import cli, service_instance
from .. import CheckVsphereException
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    isallowed,
    isbanned,
    process_retrieve_content
)

args = None

def run():
    global args
    parser = cli.Parser()
    #parser.add_optional_arguments(CheckArgument.CRITICAL_THRESHOLD)
    #parser.add_optional_arguments(CheckArgument.WARNING_THRESHOLD)
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of datastore'))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of datastore'))
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': [
                'adapter',
                'lun',
            ],
            'help': 'which runtime mode to check'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'default': 'UNKNOWN',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'help': 'exit with this status if the host is in maintenance, '
                    'default UNKNOWN, or CRITICAL if --mode maintenance'
        }
    })
    args = parser.get_args()

    si = service_instance.connect(args)
    check = Check()

    try:
        host = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve=( {'name': args.vihost} if args.vihost else None ),
            properties=["name", "configManager", "runtime.inMaintenanceMode"],
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"host {args.vihost or ''} not found")

    if host['props']['runtime.inMaintenanceMode']:
        check.exit(
            Status[args.maintenance_state],
            f"host {host['props']['name']} is in maintenance"
        )

    storage = storage_info(si, host)

    if args.mode == "adapter":
        check_adapter(check, args, storage)
    elif args.mode == "lun":
        check_lun(check, args, storage)
    elif args.mode == "path":
        check_path(check, args, storage)

def get_lun2disc(storage):
    lun2disc = {}

    for adapter in storage['storageDeviceInfo'].scsiTopology.adapter:
        for target in adapter.target:
            for lun in target.lun:
                key = lun.scsiLun
                key = key.split("-")[-1]
                lun2disc[key] = f"{lun.lun :03d}"

    return lun2disc

def check_path(check: Check, si: vim.ServiceInstance, storage):
    check.exit(Status.UNKNOWN, "Not implemented yet")
    lun2disc = get_lun2disc(storage)

    for mpInfoLun in storage['storageDeviceInfo'].multipathInfo.lun:
        for path in mpInfoLun.path:
            scsiId = path.lun.split("-")[-1]
            print(scsiId)


def check_lun(check: Check, si: vim.ServiceInstance, storage):
    lun2disc = get_lun2disc(storage)
    count = {}
    luns = storage['storageDeviceInfo'].scsiLun
    for scsi in luns:
        canonicalName = scsi.canonicalName
        scsiId = scsi.uuid
        discKey = scsi.key.split("-")[-1]
        displayName = re.sub(r'[^][\w _().-]', '', scsi.displayName)

        if isbanned(args, displayName):
            count.setdefault('ignored', 0)
            count['ignored'] += 1
            continue
        if not isallowed(args, displayName):
            count.setdefault('ignored', 0)
            count['ignored'] += 1
            continue

        operationState = "-".join(scsi.operationalState)
        if "degraded" in scsi.operationalState:
            check.add_message(Status.WARNING, f"WARNING LUN:{lun2disc[discKey]} {displayName} degraded: {operationState}")
            count.setdefault('warning', 0)
            count['warning'] += 1
        elif "ok" == scsi.operationalState[0]:
            check.add_message(Status.OK, f"OK LUN:{lun2disc[discKey]} {displayName} state: {operationState}")
            count.setdefault('ok', 0)
            count['ok'] += 1
        else:
            check.add_message(Status.CRITICAL, f"CRITICAL LUN:{lun2disc[discKey]} {displayName} state: {operationState}")
            count.setdefault('critical', 0)
            count['critical'] += 1

    (code, message) = check.check_messages(separator='\n', separator_all="\n")#, allok=okmessage)
    short = f"LUNs: {len(luns)}; " + "; ".join([ f"{x}: {count[x]}" for x in sorted(count.keys()) ])
    check.exit(
        code=code,
        message=f"{short}\n{message}"
    )



def check_adapter(check: Check, si: vim.ServiceInstance, storage):
    count = {}
    adapters = storage['storageDeviceInfo'].hostBusAdapter
    for dev in adapters:
        if  (
                isbanned(args, f"device:{dev.device}") or \
                isbanned(args, f"model:{dev.model}") or \
                isbanned(args, f"key:{dev.key}")
            ):
            count.setdefault('ignored', 0)
            count['ignored'] += 1
            continue
        if not (
            isallowed(args, f"device:{dev.device}") or \
            isallowed(args, f"model:{dev.model}") or \
            isallowed(args, f"key:{dev.key}")
           ):
            count.setdefault('ignored', 0)
            count['ignored'] += 1
            continue

        status = {
            'online': Status.OK,
            'unbound': Status.WARNING,
            'unknown': Status.CRITICAL,
            'offline': Status.CRITICAL,
        }.get(dev.status, Status.UNKNOWN)
        count.setdefault(dev.status, 0)
        count[dev.status]+=1
        check.add_message(status, f"{dev.model} {dev.device} ({dev.status})")

    short = f"Adapters {len(adapters)}; " + "; ".join([f"{x}: {count[x]}" for x in sorted(count.keys())])
    (code, message) = check.check_messages(separator="\n", separator_all="\n")#, allok=okmessage)
    check.exit(
        code=code,
        message=f"{short}\n{message}"
    )

def storage_info(si: vim.ServiceInstance, host):
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    retrieve = si.content.propertyCollector.RetrieveContents
    propspec = vmodl.query.PropertyCollector.PropertySpec(
        all=False,
        pathSet=['storageDeviceInfo'],
        type=vim.host.StorageSystem,
    )

    objs = [ObjectSpec(obj=host['props']['configManager'].storageSystem)]


    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet = objs,
        propSet = [propspec],
    )

    result = retrieve( [filter_spec] )
    storage = process_retrieve_content(result)
    return storage[0]

if __name__ == "__main__":
    run()
