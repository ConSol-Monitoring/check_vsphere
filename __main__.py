#!/usr/bin/env python3

import sys
import importlib


def run():
    cmd = None
    try:
        cmd = sys.argv.pop(1)
        sys.argv[0] = f"{sys.argv[0]} {cmd}"
    except:
        pass

    if cmd:
        try:
            runner = importlib.import_module(f"PyCheckESX.vcmd.{cmd}")
        except ModuleNotFoundError as e:
            if not e.name.startswith("vcmd."):
                raise e
            print(f"command not found: {cmd}")
            sys.exit(3)
        runner.run()
    else:
        print("Specify cmd")


if __name__ == "__main__":
    try:
        run()
    except SystemExit as e:
        if not isinstance(e.code, int) or e.code > 3:
            sys.exit(3)
    except Exception as e:
        import traceback

        print("UNKNOWN - Unhandled exception:")
        traceback.print_exc()
        sys.exit(3)
