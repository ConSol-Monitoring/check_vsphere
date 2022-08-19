#!/usr/bin/env python3

from checkvsphere.tools import cli, service_instance
from checkvsphere.tools.helper import find_entity_views
from pyVmomi import vim

parser = cli.Parser()
parser.add_required_arguments(cli.Argument.NAME)
args = parser.get_args()
si = service_instance.connect(args)

x = find_entity_views(
    si,
    vim.VirtualMachine,
    sieve={"name": args.name},
    #properties=['runtime.powerState']
    properties=['config.guestFullName','guest.hostName', 'summary']
)
