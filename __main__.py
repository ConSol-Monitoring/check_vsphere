#!/usr/bin/env python3

import sys
import importlib

cmd = None
try:
    cmd = sys.argv.pop(1)
except:
    pass

if cmd:
    runner = importlib.import_module(f'cmd.{cmd}')
    runner.run()
else:
    print("Specify cmd")
