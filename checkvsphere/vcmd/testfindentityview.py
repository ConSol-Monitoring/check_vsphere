#!/usr/bin/env python3

"""
This takes the naive approach to get all VMs and then for each VM
it uses find_entity_view to find it again to test if find_entity_views is
able to find every VM
"""

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

    vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    for vm in vm_view.view:
        vms = find_entity_views(
            si,
            vim.VirtualMachine,
            sieve={'config.name': vm.name},
            begin_entity=parentView,
            properties=['name', 'config.hardware.device', 'config.template']
        )
        assert(vm.name == vms[0]['props']['name'])
        print(vm.name, vms[0]['props']['name'])

    raise SystemExit()
