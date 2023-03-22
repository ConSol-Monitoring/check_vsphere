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
--select runtime --subselect health
"""

__cmd__ = None

import logging
import ssl
from pyVmomi import vim
from pyVim.task import WaitForTask
from http.client import HTTPConnection
from ..tools import cli, service_instance
from ..tools.helper import get_obj_by_name, get_metric, CheckArgument
from ..tools.helper import find_entity_views, get_obj_by_name, get_metric, process_retrieve_content
from monplugin import Check, Status, Threshold

try:
    import vsanmgmtObjects as vs
    import vsanapiutils as vsu
except Exception as e:
    print(f"""
{str(e)}

You need to download vsan api for python from vmware:

https://developer.vmware.com/web/sdk/8.0/vsan-python

Then take the vsanmgmtObjects.py from the bindings directory
and the vsanapiutils.py from the samples directory and place
it somewhere where your python can find it.

Also the module defusedxml must be installed:

    pip install defusedxml
    """.strip())
    raise SystemExit(3)



def run():
    parser = get_argparser()
    args = parser.get_args()

    check = Check(shortname="VSPHERE-HOSTHEALTH")

    args._si = service_instance.connect(args)

    clusters = find_entity_views(
        args._si,
        vim.ClusterComputeResource,
        begin_entity=args._si.content.rootFolder,
        properties=['name']
    )

    clusters = process_retrieve_content(list(map(lambda x: x['obj'], clusters)))

    from pprint import pprint as pp

    print(args._si.content.about)
    apiVersion = vsu.GetLatestVmodlVersion(args.host, int(args.port))
    print(apiVersion)
    vcMos =  vsu.GetVsanVcMos( #vsu.GetVsanVcMos(
        args._si._stub,
        context=sslContext(args),
        version=apiVersion
    )
    vhs = vcMos['vsan-cluster-health-system']

    for cluster in clusters:
        healthSummary = vhs.QueryClusterHealthSummary(
           cluster=cluster['moref'],
           includeObjUuids=True,
           fetchFromCache=True
        )
        print(f"{cluster['name'] } { healthSummary.overallHealth } { healthSummary.overallHealthDescription }")


def sslContext(args):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    return context


def get_argparser():
    parser = cli.Parser()
    parser.add_optional_arguments( {
        'name_or_flags': ['--maintenance-state'],
        'options': {
            'action': 'store',
            'choices': ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'],
            'default': 'UNKNOWN',
            'help': 'exit with this status if the host is in maintenance, only does something with --vimtype HostSystem'
        }
    })

    return parser


if __name__ == "__main__":
    try:
        run()
    except SystemExit as e:
        if e.code > 3 or e.code < 0:
            print("UNKNOWN EXIT CODE")
            raise SystemExit(Status.UNKNOWN)
    except Exception as e:
        print("UNKNOWN - " + str(e))
        raise SystemExit(Status.UNKNOWN)
