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
from ..tools import cli, service_instance


def run():
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
        except Exception:
            logging.debug("no server clock", exc_info=1)
            status = Status.CRITICAL
            clock = None
            if args.sessionfile:
                try:
                    logging.debug(f"deleting {args.sessionfile}")
                    os.unlink(args.sessionfile)
                except Exception:
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

if __name__ == "__main__":
    try:
        run()
    except SystemExit as e:
        if not isinstance(e.code, int) or e.code > 3 or e.code < 0:
            print("UNKNOWN EXIT CODE")
            raise SystemExit(Status.UNKNOWN)
        raise
    except Exception as e:
        print("UNKNOWN - " + str(e))
        raise SystemExit(Status.UNKNOWN)
