#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'media'

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
    parser.add_optional_arguments(cli.Argument.VIHOST)
    args = parser.get_args()
    si = service_instance.connect(args)

    check = Check(shortname='VSPHERE-MEDIA')

    if args.vihost:
        host_view = si.content.viewManager.CreateContainerView(
            si.content.rootFolder, [vim.HostSystem], True)
        try:
            parentView = next(x for x in host_view.view if x.name.lower() == args.vihost.lower())
        except:
            raise CheckVsphereException(f"host {args.vihost} not found")
    else:
        parentView = si.content.rootFolder

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    vms = find_entity_views(
        si,
        vim.VirtualMachine,
        begin_entity=parentView,
        properties=['name', 'config.hardware.device', 'config.template']
    )

    result = []

    check.add_message(
        Status.OK,
        "no connected cdrom/floppy drives found"
    )

    for vm in vms:
        match = 0
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
