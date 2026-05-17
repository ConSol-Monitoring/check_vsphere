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
check vms status
"""

__cmd__ = "vm-status"

import logging
from pyVmomi import vim
from monplugin import Check, Status
from ..tools import cli, service_instance
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    isbanned,
    isallowed,
)

check = None
args = None


def get_argparser():
    parser = cli.Parser()

    parser.add_optional_arguments(CheckArgument.BANNED("regex"))
    parser.add_optional_arguments(CheckArgument.ALLOWED("regex"))

    return parser


def run():
    global check
    global args

    parser = get_argparser()
    args = parser.get_args()

    check = Check()

    args._si = service_instance.connect(args)

    esxi_hosts = find_entity_views(
        args._si,
        vim.HostSystem,
        begin_entity=args._si.content.rootFolder,
        properties=["name", "configManager.autoStartManager"],
    )
    vms_autostart = {
        vm_power_info.key._moId: vm_power_info.startAction
        for esxi_host in esxi_hosts
        for vm_power_info in esxi_host["props"][
            "configManager.autoStartManager"
        ].config.powerInfo
    }
    vms = find_entity_views(
        args._si,
        vim.VirtualMachine,
        begin_entity=args._si.content.rootFolder,
        properties=["name", "runtime.powerState"],
    )

    for vm in vms:
        name = vm["props"]["name"]
        vm_id = vm["obj"].obj._moId
        isTemplate = vm["props"].get("config.template", None)
        autoStart = vms_autostart.get(vm_id, None) == "powerOn"
        powerState = vm["props"].get("runtime.powerState", None)
        logging.debug(
            "VM %s (#%s) is %s (autoStart=%s)", name, vm_id, powerState, autoStart
        )

        if isTemplate:
            logging.debug(f"{name} is a template vm, ignoring ...")
            continue

        if isbanned(args, name):
            logging.debug(("banned", name))
            continue

        if not isallowed(args, name):
            logging.debug(("not allowed", name))
            continue

        if powerState == "poweredOff" and autoStart:
            check.add_message(Status.CRITICAL, f"{name} is powered off")
        elif powerState == "poweredOff" and not autoStart:
            check.add_message(Status.OK, f"{name} is powered off (auto-start disabled)")
        elif powerState == "suspended":
            check.add_message(Status.WARNING, f"{name} is suspended")
        elif powerState == "poweredOn":
            check.add_message(Status.OK, f"{name} is running")
        else:
            check.add_message(
                Status.UNKNOWN,
                f"{name} status is unknown ({powerState}, "
                f"autoStart: {'enabled' if autoStart else 'disabled'})"
            )

    (code, message) = check.check_messages(separator="\n", separator_all="\n")
    check.exit(
        code=code,
        message="all auto-started VMs are running" if code == Status.OK else message,
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
