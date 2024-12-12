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
check for running vm tools
"""

__cmd__ = "vm-tools"

import logging
from collections import defaultdict

from monplugin import Check, Status
from pyVmomi import vim

from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, isbanned, isallowed, CheckArgument

check = None
args = None
portgroup = {}


def run():
    global check
    global args

    parser = cli.Parser()
    parser.add_optional_arguments(CheckArgument.BANNED(
        'regex, checked against <vm-name>'
    ))
    parser.add_optional_arguments(CheckArgument.ALLOWED(
        'regex, checked against <vm-name>'
    ))
    args = parser.get_args()

    check = Check()

    args._si = service_instance.connect(args)

    vms = find_entity_views(
        args._si,
        vim.VirtualMachine,
        begin_entity=args._si.content.rootFolder,
        properties=[
            "name",
            "runtime.powerState",
            "summary.guest",
        ],
    )

    perf_data = defaultdict(int)

    for vm in vms:
        name = vm["props"]["name"]
        isTemplate = vm["props"].get("config.template", None)
        guest_summary = vm["props"].get("summary.guest", None)
        powered = vm["props"].get("runtime.powerState", None) == "poweredOn"

        if isbanned(args, name):
            continue
        if not isallowed(args, name):
            continue

        if isTemplate:
            perf_data["VM Templates"] += 1
            logging.debug(f"{name} is a template vm, ignoring ...")
            continue

        if not powered:
            perf_data["Powered off"] += 1
            logging.debug(f"{name} is powered off")
            continue

        if guest_summary:
            if guest_summary.toolsStatus == "toolsNotInstalled":
                perf_data["VMware Tools not installed"] += 1
                logging.debug(f"{name} has no vm tools installed")
                continue
            if guest_summary.toolsRunningStatus == "guestToolsNotRunning":
                perf_data["VMware Tools not running"] += 1
                check.add_message(Status.CRITICAL, f"{name} tools not running")
                logging.debug(f"{name} tools not running")
            else:
                perf_data["VMware Tools running"] += 1

    for key, value in perf_data.items():
        check.add_perfdata(label=key, value=value, uom="")

    (code, message) = check.check_messages(separator="\n", separator_all="\n")
    check.exit(
        code=code,
        message=f"{len(vms)} VMs checked for VMware Tools state"
                if code == Status.OK
                else message,
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
