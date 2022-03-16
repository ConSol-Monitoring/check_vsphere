#!/usr/bin/env python3

import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from tools import cli, service_instance
from http.client import HTTPConnection


def run():
    parser = cli.Parser()
    #parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_required_arguments(cli.Argument.VIHOST)
    args = parser.get_args()
    si = service_instance.connect(args)

    host_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.HostSystem], True)
    try:
        host = next(x for x in  host_view.view if x.name.lower() == args.vihost.lower() )
    except:
        raise Exception(f"host {args.vihost} not found")
    vm_view = si.content.viewManager.CreateContainerView(host, [vim.VirtualMachine], True)

    result = []

    for vm in vm_view.view:
        match = 0
        if vm.config.template:
            # This vm is a template, ignore it
            continue
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualCdrom) \
            and device.connectable.connected:
                match+=1
            #print((vm,device))
        if match > 0:
            result += [ f'{vm.name} has f{match} cdrom drives connected\n' ]

    if result:
        for r in result:
            print(r)
    else:
        print('OK - no CD/DVDs connected')
    #for ds in object_view.view:
    #    print(ds)

if __name__ == "__main__":
    run()
