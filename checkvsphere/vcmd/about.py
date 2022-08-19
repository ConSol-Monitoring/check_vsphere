#!/usr/bin/env python3

"""
checks if there are any vms on a host that have connected cd or floppy drives

This is not good because vms cannot move hosts with mounted cds/floppies
"""

__cmd__ = 'about'

import logging
from ..tools.helper import find_entity_views
from pyVmomi import vim
from pyVim.task import WaitForTask
from ..tools import cli, service_instance
from http.client import HTTPConnection
from .. import CheckVsphereException


def run():
    try:
        parser = cli.Parser()
        # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
        parser.add_optional_arguments(cli.Argument.VIHOST)
        args = parser.get_args()
        si = service_instance.connect(args)
        about = si.content.about
        print(
            f'VSPHERE-ABOUT - OK - { about.fullName }, '
            f'api: { about.apiType }/{ about.apiVersion }, '
            f'product: { about.licenseProductName } { about.licenseProductVersion }'
        )
    except Exception as e:
        print(f"VSPHERE-ABOUT - ERROR - {e}")
        raise SystemExit(2)

if __name__ == "__main__":
    run()
