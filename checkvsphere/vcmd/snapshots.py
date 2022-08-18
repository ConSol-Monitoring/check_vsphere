#!/usr/bin/env python3

"""
--select runtime --subselect health
"""

__cmd__ = 'snapshots'

import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from http.client import HTTPConnection
from monplugin import Check, Status, Threshold
from ..tools import cli, service_instance
from datetime import datetime, timedelta, timezone
from ..tools.helper import (
	CheckArgument,
	find_entity_views,
	get_metric,
	get_obj_by_name,
    isbanned,
    isallowed
)

check = None
args = None

def get_argparser():
    parser = cli.Parser()
    parser.add_required_arguments( CheckArgument.CRITICAL_THRESHOLD )
    parser.add_required_arguments( CheckArgument.WARNING_THRESHOLD )
    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': ['age', 'count'],
            'help': 'check thresholds against age/count of snapshots'
        }
    })

    parser.add_optional_arguments(CheckArgument.BANNED(
        'regex, checked against <vm-name>;<snapshot-name>',
    ))
    parser.add_optional_arguments(CheckArgument.ALLOWED(
        'regex, checked against <vm-name>;<snapshot-name>',
    ))

    return parser

def check_by_age(vm, snaplist):
    vmname = vm['props']['name']
    for snap in snaplist:
        if snap.childSnapshotList:
            check_by_age(vm, snap.childSnapshotList)

        snapname = snap.name

        if isbanned(args, f'{vmname};{snapname}'):
            print(('banned', f'{vmname};{snapname}'))
            continue
        if not isallowed(args, f'{vmname};{snapname}'):
            print(('not allowed', f'{vmname};{snapname}'))
            continue

        now = datetime.now(timezone.utc)
        age = (now - snap.createTime) / timedelta(days=1)
        code = check.check_threshold(age)
        if code != Status.OK:
            check.add_message(code, f"«{snapname}» on «{vmname}» is {age:.2f} days old")
        #print((code, f"«{snapname}» on «{vmname}» is {age:.2f} days old"))

def run():
    global check
    global args
    parser = get_argparser()
    args = parser.get_args()

    check = Check(shortname="VSPHERE-SNAPSHOTS")
    check.set_threshold(warning=args.warning, critical=args.critical)

    args._si = service_instance.connect(args)

    vms = find_entity_views(
        args._si,
        vim.VirtualMachine,
        begin_entity=args._si.content.rootFolder,
        properties=['name', 'snapshot']
    )

    for vm in vms:
        name = vm['props']['name']
        if 'snapshot' not in vm['props']:
            continue

        if args.mode == 'age':
            check_by_age(vm, vm['props']['snapshot'].rootSnapshotList)

    (code, message) = check.check_messages(separator=', ')
    check.exit(
        code=code,
        message=message,
    )

if __name__ == "__main__":
    try:
        run()
    except SystemExit as e:
        if e.code > 3 or e.code < 0:
            print("UNKNOWN EXIT CODE")
            raise SystemExit(Status.UNKNOWN)
    except Exception as e:
        print("UNKNOWN - " + str(e))
        raise SystemExit(Status.UNKNOWN)
