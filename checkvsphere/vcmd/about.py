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


"""
Connects to the API and prints the version
"""

__cmd__ = 'about'

import logging
from ..tools.helper import find_entity_views
from pyVmomi import vim
from ..tools import cli, service_instance
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
            f'OK: { about.fullName }, '
            f'api: { about.apiType }/{ about.apiVersion }, '
            f'product: { about.licenseProductName } { about.licenseProductVersion }'
        )
    except vim.fault.VimFault as e:
        if hasattr(e, 'msg'):
            print(f"ERROR: {e.msg}")
        else:
            print(f"ERROR: {e}")
        raise SystemExit(2)
    except Exception as e:
        print(f"ERROR: {e}")
        raise SystemExit(2)

if __name__ == "__main__":
    run()
