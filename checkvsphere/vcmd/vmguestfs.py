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
check virtualmachine filesystems
"""

__cmd__ = "vm-guestfs"

from pyVmomi import vim, vmodl
from monplugin import Check, Status, Threshold, Range
from checkvsphere import CheckVsphereException
from checkvsphere.tools import cli, service_instance
from checkvsphere.tools.helper import (
    CheckArgument,
    find_entity_views,
    process_retrieve_content,
    isallowed,
    isbanned,
)
from checkvsphere.vcmd.datastores import Space, range_in_bytes

args = None


def run():
    global args
    parser = cli.Parser()
    parser.add_required_arguments(cli.Argument.VM_NAME)
    parser.add_optional_arguments(CheckArgument.BANNED("regex, of mountpoint"))
    parser.add_optional_arguments(CheckArgument.ALLOWED("regex, of mountpoint"))
    parser.add_optional_arguments(CheckArgument.CRITICAL_THRESHOLD)
    parser.add_optional_arguments(CheckArgument.WARNING_THRESHOLD)
    parser.add_optional_arguments(
        {
            "name_or_flags": ["--metric"],
            "options": {
                "action": "store",
                "default": "usage",
                "help": "The metric to apply the thresholds on, defaults to `usage`, can be: "
                "usage (in percent), free and used. "
                "free and used are measured in bytes. You can use one of these suffixes: "
                "kB, MB, GB for example: free_MB or used_GB",
            },
        }
    )
    args = parser.get_args()

    si = service_instance.connect(args)
    check = Check(threshold=Threshold(args.warning or None, args.critical or None))

    try:
        vm = find_entity_views(
            si,
            vim.VirtualMachine,
            begin_entity=si.content.rootFolder,
            sieve={"name": args.vm_name},
            properties=["name", "guest"],
        )[0]
    except IndexError:
        check.exit(Status.UNKNOWN, f"vm {args.vm_name} not found")

    # print(vm['props']['guest'])
    fs_info(check, vm["props"]["guest"].disk)


def fs_info(check: Check, disks):
    filtered = False
    disk_count = len(disks)

    for disk in disks:
        name = disk.diskPath
        if isbanned(args, f"{name}"):
            disk_count -= 1
            continue
        if not isallowed(args, f"{name}"):
            disk_count -= 1
            filtered = True
            continue

        try:
            space = Space(disk.capacity, disk.freeSpace)
        except ZeroDivisionError:
            check.add_message(Status.CRITICAL, f"{name} has a capacity of zero")
            continue

        for metric in ["usage", "free", "used", "capacity"]:
            opts = {}

            # Check threshold against this metric
            if args.metric.startswith(metric) and (args.warning or args.critical):
                value = space[args.metric]
                _, uom, *_ = args.metric.split("_") + ["%" if "usage" in args.metric else "B"]
                s = check.threshold.get_status(space[args.metric])

                threshold = {}
                opts["threshold"] = {}
                if args.warning:
                    threshold["warning"] = range_in_bytes(Range(args.warning), uom)
                if args.critical:
                    threshold["critical"] = range_in_bytes(Range(args.critical), uom)
                opts["threshold"] = Threshold(**threshold)

                if s != Status.OK:
                    check.add_message(s, f"{args.metric} on {name} is in state {s.name}: {value :.2f}{uom}")

            puom = "%" if metric == "usage" else "B"
            check.add_perfdata(label=f"{name} {metric}", value=space[metric], uom=puom, **opts)

    if filtered and not disk_count:
        check.add_message(Status.WARNING, "no filesystems found")

    (code, message) = check.check_messages(separator="\n")  # , allok=okmessage)
    check.exit(code=code, message=(message or "everything ok"))


if __name__ == "__main__":
    run()
