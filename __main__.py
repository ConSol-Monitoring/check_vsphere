#!/usr/bin/env python3

import sys
import importlib

def run():
    cmd = None
    try:
        cmd = sys.argv.pop(1)
        sys.argv[0] = f'{sys.argv[0]} {cmd}'
    except:
        pass

    if cmd:
        try:
            runner = importlib.import_module(f'cmd.{cmd}')
        except ModuleNotFoundError as e:
            if not e.name.startswith("cmd."):
                raise e
            print(f"command not found: {cmd}")
            sys.exit(3)
        runner.run()
    else:
        print("Specify cmd")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        import traceback
        print("Unhandled exception:")
        traceback.print_exc()
        sys.exit(3)
