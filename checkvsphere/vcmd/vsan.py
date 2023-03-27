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
vsan health
"""

__cmd__ = "vsan"

import logging
import ssl
from pyVmomi import vim
from ..tools import cli, service_instance
from ..tools.helper import CheckArgument, isallowed, isbanned
from ..tools.helper import find_entity_views, process_retrieve_content
from monplugin import Check, Status, Threshold

OK = Status.OK
WARNING = Status.WARNING
CRITICAL = Status.CRITICAL
UNKNOWN = Status.UNKNOWN

args = None

try:
    import vsanapiutils as vsu
except Exception as e:
    print(f"""
{str(e)}

You need to download vsan api for python from vmware:

https://developer.vmware.com/web/sdk/8.0/vsan-python

Then take the vsanmgmtObjects.py from the bindings directory
and the vsanapiutils.py from the samples directory and place
them somewhere where your python can find it.

Also the module defusedxml must be installed:

    pip install defusedxml
    """.strip())
    raise SystemExit(3)

# https://kb.vmware.com/s/article/2108319
# https://archive.ph/r7E96
object_health = {
    'datamove': OK,
    'healthy': OK,
    'inaccessible': CRITICAL,
    'nonavailabilityrelatedincompliance': CRITICAL, # should not be possible according to the docs
    'nonavailabilityrelatedincompliancewithpausedrebuild': WARNING,
    'nonavailabilityrelatedincompliancewithpolicypending': OK,
    'nonavailabilityrelatedincompliancewithpolicypendingfailed': WARNING,
    'nonavailabilityrelatedreconfig': OK,
    'reducedavailabilitywithactiverebuild': WARNING, # debatable
    'reducedavailabilitywithnorebuild': CRITICAL,
    'reducedavailabilitywithnorebuilddelaytimer': WARNING,
    'reducedavailabilitywithpausedrebuild': CRITICAL,
    'reducedavailabilitywithpolicypending': OK,
    'reducedavailabilitywithpolicypendingfailed': WARNING,
    'remoteAccessible': UNKNOWN, # is ignored for now
    'VsanObjectHealthState_Unknown': WARNING,
}

def run():
    global args
    parser = get_argparser()
    args = parser.get_args()

    check = Check(shortname="VSPHERE-VSAN")

    args._si = service_instance.connect(args)

    clusters = find_entity_views(
        args._si,
        vim.ClusterComputeResource,
        begin_entity=args._si.content.rootFolder,
        properties=['name']
    )

    clusters = process_retrieve_content(list(map(lambda x: x['obj'], clusters)))

    apiVersion = vsu.GetLatestVmodlVersion(args.host, int(args.port))
    vcMos =  vsu.GetVsanVcMos( #vsu.GetVsanVcMos(
        args._si._stub,
        context=sslContext(args),
        version=apiVersion
    )
    vhs = vcMos['vsan-cluster-health-system']

    for cluster in clusters:
        if isbanned(args, cluster['name']):
            continue
        if not isallowed(args, cluster['name']):
            continue

        healthSummary = vhs.QueryClusterHealthSummary(
           cluster=cluster['moref'],
           includeObjUuids=True,
           fetchFromCache=True
        )

        cluster['healthSummary'] = healthSummary

    # filter banned clusters
    clusters = list(filter(lambda x: 'healthSummary' in x, clusters))

    if args.mode == "objecthealth":
        check_objecthealth(check, clusters)
    else:
        raise Exception("WHAT?")

def check_objecthealth(check, clusters):
    for cluster in clusters:
        oh = cluster['healthSummary'].objectHealth
        for detail in oh.objectHealthDetail:
            check.add_perfdata(label=f"{cluster['name']}_{detail.health}", value=detail.numObjects)

            if detail.health == 'remoteAccessible':
                # ignore them, should be checked on the remote side
                continue

            if detail.numObjects == 0:
                continue

            state = object_health.get(detail.health, WARNING)
            check.add_message(state, f"there are {detail.numObjects} in state {detail.health} on cluster { cluster['name'] }")

    opts = {}
    if not args.verbose:
        opts['allok'] = "everything is fine"

    (status, message) = check.check_messages(separator='\n', separator_all='\n', **opts)
    check.exit(status, message)

def sslContext(args):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    return context


def get_argparser():
    parser = cli.Parser()
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of cluster'))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of cluster'))
    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': [
                'objecthealth',
            ],
            'help': 'which runtime mode to check'
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
