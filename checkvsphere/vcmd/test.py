#!/usr/bin/env python3


import omdp
import logging
from pyVmomi import vim
from pyVim.task import WaitForTask
from ..tools import cli, service_instance
from monplugin import Check, Status
from http.client import HTTPConnection

si = None


def run():
    global si
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    args = parser.get_args()
    si = service_instance.connect(args)


if __name__ == "__main__":
    run()
