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

import os
import signal
import sys
import pkgutil
import importlib
import checkvsphere.vcmd
from checkvsphere import VsphereConnectException, CheckVsphereTimeout
from pyVmomi import vim

def timeout_handler(signum, frame):
    raise CheckVsphereTimeout("Timeout reached")

def set_timeout(seconds=None, handler=None):
    if seconds is None:
        seconds = int(os.environ.get("TIMEOUT", "30"))
    signal.signal(signal.SIGALRM, (handler or timeout_handler))
    signal.alarm(seconds)

def run():
    cmd = None
    try:
        cmd = sys.argv.pop(1)
    except:
        pass

    set_timeout()

    if cmd and cmd not in ['-h', 'help', '--help']:
        mod = "".join(c for c in cmd if c.isalnum())
        try:
            runner = importlib.import_module(f"checkvsphere.vcmd.{mod}")
        except ModuleNotFoundError as e:
            if not e.name.startswith("checkvsphere.vcmd."):
                raise e
            print(f"command not found: {cmd}")
            sys.exit(3)
        try:
            sys.argv[0] = f"{sys.argv[0]} {runner.__cmd__}"
        except:
            sys.argv[0] = f"{sys.argv[0]} {cmd}"
        runner.run()
    else:
        p ={}
        cmds = set()
        for loader, name, is_pkg in pkgutil.walk_packages(checkvsphere.vcmd.__path__):
            if not is_pkg:
                full_name = checkvsphere.vcmd.__name__ + '.' + name
                p[name] = importlib.import_module(full_name)
                if hasattr(p[name], '__cmd__') and p[name].__cmd__:
                    cmds.add(p[name].__cmd__)
        print("Specify cmd, one of:\n")
        for cmd in sorted(cmds):
            print(f"  {cmd}")
        print()


def main():
    import traceback
    import logging

    if int(os.environ.get("VSPHERE_DEBUG", "0")) > 0:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            stream=sys.stderr
        )

    try:
        run()
    except VsphereConnectException as e:
        print("Cannot connect - ", end="")
        if e.__cause__ and hasattr(e.__cause__, "msg"):
            print(e.__cause__.msg)
        elif e.__cause__ and hasattr(e.__cause__, "message"):
            print(e.__cause__.message)
        elif e.__cause__:
            print(str(e.__cause__))
        else:
            print(str(e))
        sys.exit(0)
    except SystemExit as e:
        if not isinstance(e.code, int) or e.code > 3:
            sys.exit(3)
        else:
            sys.exit(e.code)
    except CheckVsphereTimeout as e:
        print("UNKNOWN - Timeout reached")
        if int(os.environ.get("VSPHERE_DEBUG", "0")) > 0:
            traceback.print_exc(file=sys.stdout)
        sys.exit(3)
    except ConnectionRefusedError as e:
        print(f"UNKNOWN - Connection refused")
        raise SystemExit(2)
    except vim.fault.VimFault as e:
        if hasattr(e, 'msg'):
            print(f"ERROR - {e.msg}")
        else:
            # in case there is no msg attribute
            # According to the docs there is
            # faultCause and faultMessage, but they are empty
            # but there is a msg attribute (which is not in the docs)
            # i don't know if it is set always
            # so fall back to the normal string representation
            print(f"ERROR - {e}")
        if int(os.environ.get("VSPHERE_DEBUG", "0")) > 0:
            traceback.print_exc(file=sys.stdout)
        raise SystemExit(3)
    except Exception as e:
        print(f"UNKNOWN - Unhandled exception: {e}")
        if int(os.environ.get("VSPHERE_DEBUG", "0")) > 0:
            traceback.print_exc(file=sys.stdout)
        raise SystemExit(3)

if __name__ == "__main__":
    main()
