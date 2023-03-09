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

class Space:
    def __init__(self, total, free):
        self.total = total
        self.free = free
        self.used = total - free
        self.usage = 100 * self.used / total

    def __getitem__(self, key):
        unit = 'B'
        if "_"  in key:
            (key, unit) = key.split('_')

        return self.__dict__[key] / Space.conversion_table[unit]

    conversion_table = {
        'B': 1,
        'kB': 10**3,
        'MB': 10**6,
        'GB': 10**9,
        'KiB': 2**10,
        'kiB': 2**10,
        'MiB': 2**20,
        'GiB': 2**30,
    }

args = None

def run():
    global args
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

    datastore_volumes_info(check, si, vm['props']['datastore'])

def datastore_volumes_info(check: Check, si: vim.ServiceInstance, datastores):
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
        if store['summary'].accessible:
            space = Space(store['summary'].capacity, store['summary'].freeSpace)
            print(f"{name} {space['total_kB'] :.2g} {space['total_KiB'] :.2g} {space['used_GiB'] :.2f}")
            check.add_perfdata(label=f"{name} usage", value=space['usage'], uom='%')
            check.add_perfdata(label=f"{name} free", value=space['free'], uom='B')
            check.add_perfdata(label=f"{name} used", value=space['used'], uom='B')
            check.add_perfdata(label=f"{name} capacity", value=space['total'], uom='B')
            check.exit(Status.OK)
        else:
            check.add_message(Status.CRITICAL, f"{name} is not accessible")



def fix_content(content):
    """
    reorganize RetrieveContents shit, so we can use it
    """
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
