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
check power state of all hosts
"""

__cmd__ = 'power-state'

import logging
from pyVmomi import vim
from monplugin import Check, Status, Threshold
from datetime import datetime, timedelta, timezone
from .. import CheckVsphereException
from ..tools import cli, service_instance
from ..tools.helper import (
    CheckArgument,
    find_entity_views,
    get_metric,
    isbanned,
    isallowed,
    process_retrieve_content
)

args = None

def get_argparser():
    parser = cli.Parser()
    parser.add_optional_arguments(CheckArgument.BANNED(
        'regex, checked against <host-name>',
    ))
    parser.add_optional_arguments(CheckArgument.ALLOWED(
        'regex, checked against <host-name>',
    ))
    parser.add_optional_arguments( CheckArgument.CRITICAL_THRESHOLD )
    parser.add_optional_arguments( CheckArgument.WARNING_THRESHOLD )
    parser.add_optional_arguments( cli.Argument.CLUSTER_NAME )
    parser.add_optional_arguments({
        'name_or_flags': ['--metric'],
        'options': {
            'action': 'store',
            'choices': ['total', 'up', 'down', 'ignored', 'up%', 'down%'],
            'default': 'down',
            'help': 'metric to apply thresholds on, defaults to "down"',
        }
    })
    return parser

def run():
    global args
    parser = get_argparser()
    args = parser.get_args()

    check = Check()
    check.set_threshold(warning=args.warning, critical=args.critical)

    args._si = service_instance.connect(args)

    begin_entity=args._si.content.rootFolder
    if args.cluster_name:
        cluster = find_entity_views(
            args._si,
            vim.ClusterComputeResource,
            properties=['name'],
            sieve={'name': args.cluster_name},
        )
        try:
            begin_entity = cluster[0]['obj'].obj
        except:
            raise CheckVsphereException(f"cluster {args.cluster_name} not found")

    hosts = find_entity_views(
        args._si,
        vim.HostSystem,
        begin_entity=begin_entity,
        properties=['name', 'runtime.powerState']
    )
    hosts = process_retrieve_content(list(map(lambda x: x['obj'], hosts)))

    total = 0
    ignored = 0
    powered = 0
    unpowered = 0

    for host in hosts:
        total += 1
        if isbanned(args, f'{host["name"]}'):
            ignored += 1
            continue
        if not isallowed(args, f'{host["name"]}'):
            ignored += 1
            continue

        message = f"powerState of { host['name'] } is { host['runtime.powerState']}"

        if host['runtime.powerState'] in ['poweredOn']: # , 'MaintenanceMode']:
            powered += 1
            check.add_message(Status.OK, message)
        else:
            unpowered += 1
            check.add_message(Status.CRITICAL, message)

    metrics = {
        'total': total,
        'up': powered,
        'down': unpowered,
        'ignored': ignored,
        'up%': 100*powered/(total - ignored) if total - ignored != 0 else -1,
        'down%': 100*unpowered/(total - ignored) if total - ignored != 0 else -1,
    }

    for l, v in metrics.items():
        opt = {}
        if l == args.metric and (args.warning or args.critical):
            opt['threshold'] = check.threshold

        check.add_perfdata(label=l, value=v, **opt)

    opt = {}
    if not args.verbose:
        opt['allok'] = 'All hosts ok'

    if args.warning or args.critical:
        code = check.check_threshold(metrics[args.metric])
        check.exit(code=code, message=f"{ total } hosts, { powered } powered, {ignored} ignored, unpowered { unpowered }")
    else:
        (code, message) = check.check_messages(separator='\n', separator_all='\n', **opt)
        check.exit(
            code=code,
            message=f"{ total } hosts, { powered } powered, {ignored} ignored, unpowered { unpowered }\n" + message,
        )
