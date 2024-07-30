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
import os
from monplugin import Status
from ..tools.helper import find_entity_views
from pyVmomi import vim
from ..tools import cli, service_instance
from .. import CheckVsphereException


def run():
    try:
        parser = cli.Parser()
        parser.add_optional_arguments({
            'name_or_flags': ['--skip-permission'],
            'options': {
                'action': 'store_true',
                'default': False,
                'help': 'skips the System.View permission check',
            }
        })

        args = parser.get_args()
        si = service_instance.connect(args)
        about = si.content.about
        status = Status.OK
        clock = True
        if not args.skip_permission:
            try:
                clock = si.serverClock
            except Exception as e:
                logging.debug("no server clock", exc_info=1)
                status = Status.CRITICAL
                clock = None
                if args.sessionfile:
                    try:
                        logging.debug(f"deleting {args.sessionfile}")
                        os.unlink(args.sessionfile)
                    except Exception as e:
                        logging.debug(f"unlink {args.sessionfile} failed", exc_info=1)

        out = (
            f'{status.name}: '
            f'{ "No System.View permission, " if not clock  else "" }'
            f'{ about.fullName }, '
            f'api: { about.apiType }/{ about.apiVersion }, '
            f'product: { about.licenseProductName } { about.licenseProductVersion }'
        )
        print(out)
        raise SystemExit(status.value)
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
