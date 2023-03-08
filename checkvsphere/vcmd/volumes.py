#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'volumes'

from pyVmomi import vim, vmodl
from monplugin import Check, Status
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, CheckArgument, isbanned
from .. import CheckVsphereException

def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_required_arguments(CheckArgument.VIMNAME)
    parser.add_required_arguments(CheckArgument.VIMTYPE)
    args = parser.get_args()

    si = service_instance.connect(args)
    check = Check(shortname='VSPHERE-VOL')

    #objview = si.content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    #print(objview)
    #return

    vimtype = getattr(vim, args.vimtype)

    try:
        vm = find_entity_views(
            si,
            vimtype,
            begin_entity=si.content.rootFolder,
            sieve={'name': args.vimname},
            properties=["name", "datastore"],
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"host {args.vihost} not found")

    datastore_volumes_info(si, vm['props']['datastore'])

def datastore_volumes_info(si, datastores):
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    retrieve = si.content.propertyCollector.RetrieveContents
    propspec = vmodl.query.PropertyCollector.PropertySpec(
        all=False,
        pathSet=['summary', 'info'],
        type=vim.Datastore
    )

    objs = []
    for store in datastores:
        objs.append(ObjectSpec(obj=store))

    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet = objs,
        propSet = [propspec],
    )

    result = retrieve( [filter_spec] )
    stores = fix_content(result)

    for store in stores:
        name = store['summary'].name
        volume_type = store['summary'].type
        print((name, volume_type))
        if store['summary'].accessible:
            print(('a', name))




def fix_content(content):
    objs = []
    for o in content:
        d = {}
        d['moref'] = o.obj
        for prop in o.propSet:
            d[prop.name] = prop.val
        objs.append(d)
    return objs


if __name__ == "__main__":
    run()
