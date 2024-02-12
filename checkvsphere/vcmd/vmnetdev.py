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
check network devices of vms
"""

__cmd__ = "vm-net-dev"

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
    isallowed,
)

check = None
args = None
portgroup = {}


def get_argparser():
    parser = cli.Parser()
    parser.add_required_arguments(
        {
            "name_or_flags": ["--mode"],
            "options": {
                "action": "store",
                "choices": ["start-unconnected"],
                "help": "check for vms that have network cards configured "
                "that are not connected on startup."
                '--exclude and --include match against a string like "vmname;Network adapter 1"',
            },
        }
    )

    parser.add_optional_arguments(CheckArgument.BANNED("regex"))
    parser.add_optional_arguments(CheckArgument.ALLOWED("regex"))

    return parser


def check_start_not_connected(vm):
    vmname = vm["props"]["name"]

    for d in vm["props"]["config.hardware"].device:
        if "VirtualEthernetCard" in str(type(d.backing)):
            probe = f"{vmname};{d.deviceInfo.label}"

            if isbanned(args, probe):
                logging.debug(("banned", probe))
                continue

            if not isallowed(args, probe):
                logging.debug(("not allowed", probe))
                continue

            if not d.connectable.connected:
                logging.debug(("running and disconnected", probe))
                continue

            if not d.connectable.startConnected:
                check.add_message(
                    Status.CRITICAL, f"Connect At Power On is off for {probe}"
                )


def run():
    global check
    global args

    parser = get_argparser()
    args = parser.get_args()

    check = Check()

    args._si = service_instance.connect(args)

    vms = find_entity_views(
        args._si,
        vim.VirtualMachine,
        begin_entity=args._si.content.rootFolder,
        properties=["name", "runtime.powerState", "config.template", "config.hardware"],
    )

    for vm in vms:
        name = vm["props"]["name"]
        isTemplate = vm["props"].get("config.template", None)
        powered = vm["props"].get("runtime.powerState", None) == "poweredOn"

        if not powered:
            logging.debug(f"{name} is powered off")
            continue

        if isTemplate:
            logging.debug(f"{name} is a template vm, ignoring ...")
            continue

        if args.mode == "start-unconnected":
            check_start_not_connected(vm)

    (code, message) = check.check_messages(separator="\n", separator_all="\n")
    check.exit(
        code=code,
        message=f"all checks ok" if code == Status.OK else message,
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
