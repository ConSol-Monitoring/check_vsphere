#!/usr/bin/env python3

import sys
import importlib

cmd = None
try:
    cmd = sys.argv.pop(1)
except:
    pass

if cmd:
    try:
        runner = importlib.import_module(f'cmd.{cmd}')
    except:
        print(f"{cmd} does not exist")
        sys.exit(3)
    runner.run()
else:
    print("Specify cmd")
