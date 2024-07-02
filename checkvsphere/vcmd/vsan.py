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

# https://kb.vmware.com/s/article/2108319
# https://archive.ph/r7E96
object_health = {
    'datamove': OK,
    'healthy': OK,
    'inaccessible': CRITICAL,
    'nonavailabilityrelatedincompliance': CRITICAL, # should not be possible according to the docs
    'nonavailabilityrelatedincompliancewithpausedrebuild': WARNING,
    'nonavailabilityrelatedincompliancewithpolicypending': OK,
    'nonavailabilityrelatedincompliancewithpolicypendingfailed': CRITICAL,
    'nonavailabilityrelatedreconfig': OK,
    'reducedavailabilitywithactiverebuild': WARNING, # debatable
    'reducedavailabilitywithnorebuild': CRITICAL,
    'reducedavailabilitywithnorebuilddelaytimer': WARNING,
    'reducedavailabilitywithpausedrebuild': CRITICAL,
    'reducedavailabilitywithpolicypending': OK,
    'reducedavailabilitywithpolicypendingfailed': CRITICAL,
    'remoteAccessible': UNKNOWN, # is ignored for now
    'VsanObjectHealthState_Unknown': WARNING,
}

def run():
    global args
    import_vsan()
    parser = get_argparser()
    args = parser.get_args()

    check = Check()

    args._si = service_instance.connect(args)

    clusters = find_entity_views(
        args._si,
        vim.ClusterComputeResource,
        begin_entity=args._si.content.rootFolder,
        properties=['name', 'configurationEx']
    )

    clusters = process_retrieve_content(list(map(lambda x: x['obj'], clusters)))

    apiVersion = vsu.GetLatestVmodlVersion(args.host, int(args.port))
    vcMos =  vsu.GetVsanVcMos( #vsu.GetVsanVcMos(
        args._si._stub,
        context=sslContext(args),
        version=apiVersion
    )
    vhs = vcMos['vsan-cluster-health-system']

    clusters = list(filter(lambda x: x['configurationEx'].vsanConfigInfo.enabled, clusters))

    for cluster in clusters:
        if isbanned(args, cluster['name'], 'exclude'):
            continue
        if not isallowed(args, cluster['name'], 'include'):
            continue

        fields = ['vsanConfig']
        if args.mode == 'objecthealth':
            fields.append('objectHealth')
        if args.mode == 'healthtest':
            fields.append('groups')

        healthSummary = vhs.QueryClusterHealthSummary(
           cluster=cluster['moref'],
           includeObjUuids=False,
           fetchFromCache=args.cache,
           fields=fields
        )

        cluster['healthSummary'] = healthSummary

    # filter banned clusters
    clusters = list(filter(lambda x: 'healthSummary' in x, clusters))

    if args.mode == "objecthealth":
        check_objecthealth(check, clusters)
    elif args.mode == "healthtest":
        check_healthtest(check, clusters)
    else:
        raise Exception("WHAT?")

def check_healthtest(check, clusters):
    for cluster in clusters:
        #print((cluster['name'], cluster))
        if not cluster['healthSummary'].vsanConfig.vsanEnabled:
            continue
        for group in cluster['healthSummary'].groups:
            if isbanned(args, group.groupName, 'exclude_group'):
                continue
            if not isallowed(args, group.groupName, 'include_group'):
                continue
            for test in group.groupTests:
                if isbanned(args, test.testName, 'exclude_test'):
                    continue
                if not isallowed(args, test.testName, 'include_test'):
                    continue
                check.add_message(
                    health2state(test.testHealth),
                    f"Cluster: {cluster['moref'].name} Group: { group.groupName } Status: { test.testHealth } Test: { test.testName }"
                )

    opts = {}
    if not args.verbose:
        opts['allok'] = "everything is fine"

    (status, message) = check.check_messages(separator='\n', separator_all='\n', **opts)
    check.exit(status, message)



def check_objecthealth(check, clusters):
    for cluster in clusters:
        oh = cluster['healthSummary'].objectHealth
        if not cluster['healthSummary'].vsanConfig.vsanEnabled:
            check.add_message(OK, f"cluster {cluster['name']} doesn't have objectHealth")
            continue

        if oh is None:
            # cluster doesn't have objectHealth
            check.add_message(OK, f"cluster {cluster['name']} doesn't have objectHealth")
            continue

        for detail in oh.objectHealthDetail:
            check.add_perfdata(label=f"{cluster['name']} {detail.health}", value=detail.numObjects)

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
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of cluster', name=['--exclude']))
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of group (only with --mode healthtest)', name=['--exclude-group']))
    parser.add_optional_arguments(CheckArgument.BANNED('regex, name of test (only with --mode healthtest)', name=['--exclude-test']))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of cluster', name=['--include']))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of group (only with --mode healthtest)', name=['--include-group']))
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex, name of test (only with --mode healthtest)', name=['--include-test']))
    parser.add_optional_arguments({
        'name_or_flags': ['--cache'],
        'options': {
            'action': 'store_true',
            'help': 'tell the api to return cached data if available'
        }
    })
    parser.add_required_arguments( {
        'name_or_flags': ['--mode'],
        'options': {
            'action': 'store',
            'choices': [
                'objecthealth',
                'healthtest',
            ],
            'help': 'which runtime mode to check'
        }
    })

    return parser

def import_vsan():
    global vsu
    try:
        import vsanapiutils as vsu
    except Exception as e:
        print((
            f"""{str(e)}\n\n"""
            "pyVmomi is too old, at least 8.0.3.0.1 is required"
        ).strip())
        raise SystemExit(3)

def health2state(color):
    color = color or ""
    return {
        "green": Status.OK,
        "yellow": Status.WARNING,
        "red": Status.CRITICAL,
        'unknown': Status.WARNING,
        'info': Status.OK,
        'skipped': Status.OK,
        # think about it more if this ever happens, according to the API it could
        # but it doesn't say what that means, so we investigate this once we see it
        # in the wild
        "": Status.WARNING,
    }.get(color.lower(), Status.WARNING)

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
