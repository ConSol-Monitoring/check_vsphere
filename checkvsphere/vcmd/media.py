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
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'media'

from pyVmomi import vim
from monplugin import Check, Status
from checkvsphere import CheckVsphereException
from checkvsphere.tools import cli, service_instance
from checkvsphere.tools.helper import find_entity_views, isbanned, isallowed, CheckArgument

def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex match against vm name'))
    parser.add_optional_arguments(CheckArgument.BANNED('regex match against vm name'))
    args = parser.get_args()
    si = service_instance.connect(args)

    check = Check()

    if args.vihost:
        host = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve={'name': args.vihost},
        )
        if not host:
            raise CheckVsphereException(f"host {args.vihost} not found")
        parentView = host[0]['obj'].obj
    else:
        parentView = si.content.rootFolder

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    vms = find_entity_views(
        si,
        vim.VirtualMachine,
        begin_entity=parentView,
        properties=['name', 'config.hardware.device', 'config.template']
    )

    check.add_message(
        Status.OK,
        "no connected cdrom/floppy drives found"
    )

    for vm in vms:
        match = 0
        if isbanned(args, vm['props']['name']):
            continue
        if not isallowed(args, vm['props']['name']):
            continue

        if vm['props']['runtime.powerState'] != 'poweredOn':
            # it's powered off, api is unreliable
            # config.hardware or config.template might be missing
            continue

        if vm['props']['config.template']:
            # This vm is a template, ignore it
            continue

        for device in vm['props']['config.hardware.device']:
            if \
                (isinstance(device, vim.vm.device.VirtualCdrom)
                 or isinstance(device, vim.vm.device.VirtualFloppy)) \
                    and device.connectable.connected:
                match += 1
        if match > 0:
            check.add_message(
                Status.CRITICAL,
                f'{vm["props"]["name"]} has cdrom/floppy drives connected'
            )

    (code, message) = check.check_messages(separator=' - ')
    check.exit(
        code=code,
        message=message
    )


if __name__ == "__main__":
    run()
