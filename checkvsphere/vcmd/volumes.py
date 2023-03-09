#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'volumes'

from pyVmomi import vim, vmodl
from monplugin import Check, Status, Threshold, Range
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, CheckArgument, isbanned, isallowed
from .. import CheckVsphereException

class Space:
    def __init__(self, capacity, free):
        self.capacity = capacity
        self.free = free
        self.used = capacity - free
        self.usage = 100 * self.used / capacity

    def __getitem__(self, key):
        unit = 'B'
        if "_"  in key:
            (key, unit) = key.split('_')

        # Don't do conversion on usage
        if key == "usage":
            return self.__dict__[key]

        return self.__dict__[key] / Space.conversion_table[unit]

    conversion_table = {
        '%': 1,
        'B': 1,
        'kB': 2**10,
        'MB': 2**20,
        'GB': 2**30,
    }

def range_in_bytes(r: Range, uom):
    start = r.start
    end = r.end

    start *= Space.conversion_table[uom]
    end *= Space.conversion_table[uom]

    return ('' if r.outside else '@') + \
        ('~' if start == float('-inf') else str(start)) + \
        ":" + ('' if end == float('+inf') else str(end))

args = None

def run():
    global args
    parser = cli.Parser()
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of datastore'))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of datastore'))
    parser.add_required_arguments(CheckArgument.VIMNAME)
    parser.add_required_arguments(CheckArgument.VIMTYPE)
    parser.add_optional_arguments(CheckArgument.CRITICAL_THRESHOLD)
    parser.add_optional_arguments(CheckArgument.WARNING_THRESHOLD)
    parser.add_optional_arguments({
        'name_or_flags': ['--metric'],
        'options': {
            'action': 'store',
            'default': 'usage',
            'help': 'The metric to apply the thresholds on, defaults to `usage`, can be: '
                    'usage (in percent), free and used. '
                    'free and used are measured in bytes. You can one of these suffixes: '
                    'kB, MB, GB for example: free_MB or used_GB'
        }
    })
    args = parser.get_args()

    si = service_instance.connect(args)
    check = Check(shortname='VSPHERE-VOL', threshold = Threshold(args.warning or None, args.critical or None))

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

    values_to_check = []

    for store in stores:

        name = store['summary'].name
        volume_type = store['summary'].type

        if isbanned(args, f"{name}"):
            continue
        if not isallowed(args, f"{name}"):
            continue

        if not store['summary'].accessible:
            check.add_message(Status.CRITICAL, f"{name} is not accessible")
            continue

        space = Space(store['summary'].capacity, store['summary'].freeSpace)
        for metric in ['usage', 'free', 'used', 'capacity']:
            opts = {}

            # Check threshold against this metric
            if args.metric.startswith(metric) and (args.warning or args.critical):
                value = space[args.metric]
                _, uom, *_ = (args.metric.split('_') + ['%' if 'usage' in args.metric else 'B'])
                values_to_check.append(value)
                s = check.threshold.get_status(space[args.metric])
                opts['threshold'] = {}
                threshold = {}
                if args.warning:
                    threshold['warning'] = range_in_bytes(Range(args.warning), uom)
                if args.critical:
                    threshold['critical'] = range_in_bytes(Range(args.critical), uom)

                opts['threshold'] = Threshold(**threshold)

                if s != Status.OK:
                    check.add_message(s, f"{args.metric} on {name} is in state {s.name}: {value :.2f}{uom}")

            puom = '%' if metric == 'usage' else 'B'
            check.add_perfdata(label=f"{name} {metric}", value=space[metric], uom=puom, **opts)

    (code, message) = check.check_messages(separator="\n", separator_all='\n')#, allok=okmessage)
    check.exit(
        code=code,
        message=( message or "everything ok" )
    )


def fix_content(content):
    """
    reorganize RetrieveContents shit, so we can use it.
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
