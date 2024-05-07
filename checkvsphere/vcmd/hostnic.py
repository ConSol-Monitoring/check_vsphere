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
Check NICs on the host
"""

__cmd__ = 'host-nic'

import logging
from pyVmomi import vim
from monplugin import Check, Status
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, CheckArgument, isbanned
from .. import CheckVsphereException

def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments(CheckArgument.BANNED(
        'regex, check against nic name'
    ))
    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'default': 'UNKNOWN',
            'help': 'exit with this status if the host is in maintenance, default UNKNOWN'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--unplugged-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL'],
            'default': 'WARNING',
            'help': 'treat unplugged nics with that status code'
        }
    })

    args = parser.get_args()

    si = service_instance.connect(args)
    check = Check()

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    try:
        vm = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve=({'name': args.vihost} if args.vihost else None),
            properties=["name", "configManager.networkSystem", "runtime.inMaintenanceMode"]
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"host {args.vihost or ''} not found")

    result = []

    if vm['props']['runtime.inMaintenanceMode']:
        check.exit(
            Status[args.maintenance_state],
            f"host {vm['props']['name']} is in maintenance"
        )

    network_system = vm["props"]["configManager.networkSystem"]
    network_info = network_system.networkInfo

    if not network_info:
        check.exit(
            Status.CRITICAL,
            f"{args.vihost} has no network info in the API"
        )

    # physical nics
    pnics = {}
    switches = []
    for pnic in network_info.pnic:
        pnics[pnic.key] = pnic

    if network_info.vswitch:
        switches.extend(network_info.vswitch)
    if network_info.proxySwitch:
        switches.extend(network_info.proxySwitch)

    for switch in switches:
        for nic in (switch.pnic or []):
            if isbanned(args, pnics[str(nic)].device):
                continue

            if not pnics[nic].linkSpeed:
                status = Status[args.unplugged_state]
                appendix=""
                if status == Status.OK:
                    appendix = " , but ok due to `--unplugged_state OK`"
                check.add_message(status, f"{pnics[str(nic)].device} is unplugged{appendix}")
            else:
                check.add_message(Status.OK, f"{pnics[str(nic)].device} is ok")


    okmessage = "All nics connected"

    (code, message) = check.check_messages(separator="\n", separator_all='\n')#, allok=okmessage)
    check.exit(
        code=code,
        message=( message or "everything ok" )
    )

if __name__ == "__main__":
    run()
