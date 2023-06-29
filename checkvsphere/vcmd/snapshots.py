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
check age or number of vm snapshots
"""

__cmd__ = 'snapshots'

import logging
from pyVmomi import vim
from monplugin import Check, Status, Threshold
from ..tools import cli, service_instance
from datetime import datetime, timedelta, timezone
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    get_metric,
    isbanned,
    isallowed
)

check = None
args = None

def get_argparser():
    parser = cli.Parser()
    parser.add_optional_arguments( CheckArgument.CRITICAL_THRESHOLD )
    parser.add_optional_arguments( CheckArgument.WARNING_THRESHOLD )
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

def count_snapshots(vm, snaplist):
    count = 0
    vmname = vm['props']['name']

    for snap in snaplist:

        if snap.childSnapshotList:
            count+=count_snapshots(vm, snap.childSnapshotList)

        snapname = snap.name

        if isbanned(args, f'{vmname};{snapname}'):
            logging.debug(('banned', f'{vmname};{snapname}'))
            continue
        if not isallowed(args, f'{vmname};{snapname}'):
            logging.debug(('not allowed', f'{vmname};{snapname}'))
            continue

        count+=1

    return count

def check_by_age(vm, snaplist):
    vmname = vm['props']['name']
    for snap in snaplist:
        if snap.childSnapshotList:
            check_by_age(vm, snap.childSnapshotList)

        snapname = snap.name

        if isbanned(args, f'{vmname};{snapname}'):
            logging.debug(('banned', f'{vmname};{snapname}'))
            continue
        if not isallowed(args, f'{vmname};{snapname}'):
            logging.debug(('not allowed', f'{vmname};{snapname}'))
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

    if not (args.warning or args.critical):
        raise Exception("at least one of --warning or --critical is required")

    check = Check()
    check.set_threshold(warning=args.warning, critical=args.critical)

    args._si = service_instance.connect(args)

    vms = find_entity_views(
        args._si,
        vim.VirtualMachine,
        begin_entity=args._si.content.rootFolder,
        properties=['name', 'snapshot', 'resourcePool', 'config.template']
    )

    for vm in vms:
        name = vm['props']['name']
        isTemplate = vm['props'].get('config.template', None)

        if 'snapshot' not in vm['props']:
            logging.debug(f"vm {name} has no snapshots")
            continue

        if isTemplate:
            logging.debug(f"{name} is a template vm, ignoring ...")
            continue

        adj = None
        if args.mode == 'age':
            adj = 'old'
            check_by_age(vm, vm['props']['snapshot'].rootSnapshotList)
        elif args.mode == 'count':
            adj = 'many'
            count = count_snapshots(vm, vm['props']['snapshot'].rootSnapshotList)
            code = check.check_threshold(count)
            if code != Status.OK:
                check.add_message(code, f"«{name}» has {count} snapshots")
        else:
            raise RuntimeError("Unknown mode {args.mode}")

    (code, message) = check.check_messages(separator='\n', separator_all='\n')
    check.exit(
        code=code,
        message=f"snapshots ok" if code == Status.OK else f"too {adj} snapshots found\n" + message,
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
