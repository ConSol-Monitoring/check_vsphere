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
checks the health of a cluster in vsphere
"""

__cmd__ = 'cluster-health'

import logging
from pyVmomi import vim, vmodl
from pprint import pprint as pp
from monplugin import Check, Status
from ..tools import cli, service_instance
from ..tools.cluster_health import check_cluster_health
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    process_retrieve_content
)

args = None

def host_is_failed(args, h):
    name = h['name']
    faulty = set(args.faulty)
    overall = h['overallStatus'].capitalize()

    if f'overallStatus{overall}' in faulty:
        logging.debug(f"{name} overallStatus {h['overallStatus']}")
        return True

    if "inMaintenance" in faulty and h['runtime'].inMaintenanceMode:
        logging.debug(f"{name} in maintenance")
        return True

    if "inQuarantine" in faulty and h['runtime'].inQuarantineMode:
        logging.debug(f"{name} quarantined")
        return True

    if "notconnected" in faulty and h['runtime'].connectionState != "connected":
        logging.debug(f"{name} connectionState {h['runtime'].connectionState}")
        return True

    return False

def host_in_standby(h):
    r = h['runtime'].standbyMode == "none"
    if not r:
        logging.debug(f"{h['name']} in standby, not considered part of cluster")

def run():
    global args
    parser = cli.Parser()
    parser.add_required_arguments(CheckArgument.CLUSTER_NAME)
    parser.add_required_arguments(CheckArgument.CLUSTER_THRESHOLD)
    parser.add_optional_arguments({
        'name_or_flags': ['--nostandby'],
        'options': {
            'action': 'store_true',
            'default': False,
            'help': 'Standby nodes are not considered part of the cluster'
        }
    })
    parser.add_optional_arguments({
        'name_or_flags': ['--faulty'],
        'options': {
            'action': 'append',
            'default': [],
            'help': 'Things that are considered faulty (*=default): *inMaintenance, '
                    '*notconnected, inStandby, inQurantine, overallStatusRed, '
                    'overallStatusYellow, overallStatusGrey'
        }
    })
    args = parser.get_args()
    if not args.faulty:
        args.faulty = ['notconnected', 'inMaintenance']

    # if yellow is faulty, red is definitly faulty as well
    if 'overallStatusYellow' in args.faulty:
        args.faulty.append(['overallStatusRed'])

    si = service_instance.connect(args)
    check = Check()
    hosts = []

    try:
        res = find_entity_views(
            si,
            vim.ClusterComputeResource,
            begin_entity=si.content.rootFolder,
            sieve=( {'name': args.cluster_name} ),
            properties=["name", "host"],
        )[0]
        hosts = res['props']['host']
    except IndexError:
        check.exit(Status.UNKNOWN, f"{args.cluster_name} not found")

    if not hosts:
        check.exit(Status.CRITICAL, "Cluster is empty")

    hosts = resolve_hosts(si, hosts)
    # Hosts in standby are not considered part of the cluster
    hosts = list(filter(lambda h: not host_in_standby(h), hosts))

    cluster_size = len(hosts)
    failed_members = sum(1 for h in hosts if host_is_failed(args, h))
    cluster_state = check_cluster_health(failed_members, cluster_size, args.cluster_threshold)
    check.exit(
        cluster_state,
        f"{cluster_size-failed_members} out of {cluster_size} cluster members are ok"
    )


def resolve_hosts(si, hosts):
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    retrieve = si.content.propertyCollector.RetrieveContents
    propspec = vmodl.query.PropertyCollector.PropertySpec(
        all=False,
        pathSet=['name', 'overallStatus', 'runtime'],
        type=vim.HostSystem
    )
    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet = list(map(lambda x: ObjectSpec(obj=x), hosts)),
        propSet = [propspec],
    )
    objs = retrieve( [filter_spec] )

    def props_mapping(obj):
        props = {}
        for p in obj.propSet:
            props[p.name] = p.val
        return props

    result = list(map(lambda x: props_mapping(x), objs))
    #pp(result)
    return result

if __name__ == "__main__":
    run()
