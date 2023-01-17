#!/usr/bin/env python3

import os
import signal
import sys
import pkgutil
import importlib
import checkvsphere.vcmd
from checkvsphere import VsphereConnectException, CheckVsphereTimeout

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

    if cmd:
        mod = "".join(c for c in cmd if c.isalnum())
        try:
            runner = importlib.import_module(f"checkvsphere.vcmd.{mod}")
        except ModuleNotFoundError as e:
            if not e.name.startswith("vcmd."):
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

    try:
        run()
    except VsphereConnectException as e:
        print("Cannot connect")
        traceback.print_exc(file=sys.stdout)
        sys.exit(0)
    except SystemExit as e:
        if not isinstance(e.code, int) or e.code > 3:
            sys.exit(3)
        else:
            sys.exit(e.code)
    except CheckVsphereTimeout as e:
        print("UNKOWN - Timout reached")
        traceback.print_exc(file=sys.stdout)
        sys.exit(3)
    except Exception as e:
        print("UNKNOWN - Unhandled exception:")
        traceback.print_exc(file=sys.stdout)
        sys.exit(3)

if __name__ == "__main__":
    main()
