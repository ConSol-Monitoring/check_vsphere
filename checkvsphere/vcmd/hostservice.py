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
check services on host
"""

__cmd__ = 'host-service'

import logging
from pyVmomi import vim, vmodl
from monplugin import Check, Status
from ..tools import cli, service_instance
from .. import CheckVsphereException
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    isallowed,
    isbanned,
    process_retrieve_content
)

def run():
    global args
    parser = cli.Parser()
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of datastore'))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of datastore'))
    parser.add_optional_arguments(cli.Argument.VIHOST)
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

    count = {
        'running': 0,
        'not running': 0,
    }
    serviceSystem = service_system(si, host)
    for service in serviceSystem['serviceInfo'].service:
        serviceName = service.key
        serviceState = service.running

        if isbanned(args, serviceName):
            continue
        if not isallowed(args, serviceName):
            continue

        if not serviceState:
            check.add_message(Status.CRITICAL, f"{serviceName} not running")
            count['not running']+=1
        else:
            check.add_message(Status.OK, f"{serviceName} running")
            count['running']+=1

    (status, message) = check.check_messages(separator="\n", separator_all="\n")
    short = f"running: {count['running']}; not running: {count['not running']}"
    check.exit(status, f"{short}\n{message}")

def service_system(si: vim.ServiceInstance, host):
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    retrieve = si.content.propertyCollector.RetrieveContents
    propspec = vmodl.query.PropertyCollector.PropertySpec(
        all=False,
        pathSet=['serviceInfo'],
        type=vim.host.ServiceSystem
    )

    objs = [ObjectSpec(obj=host['props']['configManager'].serviceSystem)]

    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet = objs,
        propSet = [propspec],
    )

    result = retrieve( [filter_spec] )
    service_system = process_retrieve_content(result)
    return service_system[0]

if __name__ == "__main__":
    run()
