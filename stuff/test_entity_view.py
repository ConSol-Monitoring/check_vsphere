#!/usr/bin/env python3

from PyCheckESX.tools import cli, service_instance
from PyCheckESX.tools.helper import find_entity_views
from pyVmomi import vim

parser = cli.Parser()
args = parser.get_args()
si = service_instance.connect(args)

x = find_entity_views(
    si,
    vim.VirtualMachine,
    sieve={"name": "lausser1"},
    properties=['config.guestFullName','guest.hostName', 'config.hardware.device', 'runtime.powerState']
)
