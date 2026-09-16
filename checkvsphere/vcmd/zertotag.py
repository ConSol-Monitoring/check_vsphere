#!/usr/bin/env python3

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
Checks whether eligible VMs have a Zerto DRaaS protection tag.

The missing Zerto tag is a critical issue because it highlights that a
new system lacks DRaaS replication protection. To ensure compliance,
every virtual machine must be assigned a Zerto tag identified by the
'Zerto - Protection Automation' category.
"""

__cmd__ = 'zertotag'

import logging
import os
import re

import requests
import urllib3

from monplugin import Check, Status
from pyVmomi import vim

from checkvsphere import CheckVsphereException
from checkvsphere.tools import cli, service_instance
from checkvsphere.tools.helper import CheckArgument, find_entity_views, isallowed, isbanned


ZERTOTAG_CATEGORY = 'Zerto - Protection Automation'
ZERTOTAG_CATEGORY_PATTERN = re.compile(r'Zerto [-\u2013] Protection Automation')


class TaggingApiError(Exception):
    """Raised when the vCenter tagging API cannot be used safely."""


def get_session_verify(args):
    if args.disable_ssl_verification:
        logging.debug('Zerto tag check: REST SSL verification disabled')
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False

    ca_bundle = os.environ.get('SSL_CA_FILE') or os.environ.get('SSL_CA_PATH')
    if ca_bundle:
        logging.debug('Zerto tag check: REST SSL verification uses configured CA bundle')
        return ca_bundle

    logging.debug('Zerto tag check: REST SSL verification uses system trust store')
    return True


def get_response_value(response, operation):
    if response.status_code != 200:
        raise TaggingApiError('{} failed (HTTP {})'.format(operation, response.status_code))

    try:
        payload = response.json()
    except ValueError as error:
        raise TaggingApiError('{} returned invalid JSON'.format(operation)) from error

    if not isinstance(payload, dict) or 'value' not in payload:
        raise TaggingApiError('{} returned an invalid response'.format(operation))

    return payload['value']


def get_protected_vm_ids(args):
    """Return VM managed-object IDs assigned a tag in the Zerto category."""
    base_url = 'https://{}:{}'.format(args.host, args.port)
    session = requests.Session()
    session.verify = get_session_verify(args)
    rest_api_calls = 0

    def request(method, url, **kwargs):
        nonlocal rest_api_calls
        rest_api_calls += 1
        return getattr(session, method)(url, **kwargs)

    try:
        logging.debug('Zerto tag check: authenticating to vCenter REST API at %s', base_url)
        response = request(
            'post',
            '{}/rest/com/vmware/cis/session'.format(base_url),
            auth=(args.user, args.password),
        )
        session_token = get_response_value(response, 'REST authentication')
        if not isinstance(session_token, str) or not session_token:
            raise TaggingApiError('REST authentication returned an invalid session token')
        session.headers.update({'vmware-api-session-id': session_token})
        logging.debug('Zerto tag check: vCenter REST authentication succeeded')

        category_ids = get_response_value(
            request('get', '{}/rest/com/vmware/cis/tagging/category'.format(base_url)),
            'Category listing',
        )
        if not isinstance(category_ids, list):
            raise TaggingApiError('Category listing returned an invalid response')
        logging.debug('Zerto tag check: found %d tag categories', len(category_ids))

        category_id = None
        for current_category_id in category_ids:
            category = get_response_value(
                request(
                    'get',
                    '{}/rest/com/vmware/cis/tagging/category/id:{}'.format(
                        base_url,
                        current_category_id,
                    )
                ),
                'Category lookup',
            )
            if not isinstance(category, dict):
                raise TaggingApiError('Category lookup returned an invalid response')
            category_name = category.get('name')
            if not isinstance(category_name, str):
                raise TaggingApiError('Category lookup returned an invalid response')
            logging.debug(
                'Zerto tag check: category id=%s name=%r',
                current_category_id,
                category_name,
            )
            if ZERTOTAG_CATEGORY_PATTERN.fullmatch(category_name):
                category_id = current_category_id
                break

        if category_id is None:
            logging.debug('Zerto tag check: required category was not found')
            return None, rest_api_calls
        logging.debug('Zerto tag check: found required category id=%s', category_id)

        tags_url = '{}/rest/com/vmware/cis/tagging/tag?~action=list-tags-for-category'.format(
            base_url
        )
        tag_ids = get_response_value(
            request('post', tags_url, json={'category_id': category_id}),
            'Tag listing',
        )
        if not isinstance(tag_ids, list):
            raise TaggingApiError('Tag listing returned an invalid response')
        logging.debug(
            'Zerto tag check: found %d tags in required category: %s',
            len(tag_ids),
            tag_ids,
        )
        if not tag_ids:
            return set(), rest_api_calls

        associations = get_response_value(
            request(
                'post',
                '{}/rest/com/vmware/cis/tagging/tag-association?~action='
                'list-attached-objects-on-tags'.format(base_url),
                json={'tag_ids': tag_ids},
            ),
            'Tag association lookup',
        )
    except requests.RequestException as error:
        raise TaggingApiError('REST request failed: {}'.format(error)) from error

    if not isinstance(associations, list):
        raise TaggingApiError('Tag association lookup returned an invalid response')
    logging.debug('Zerto tag check: received %d tag association results', len(associations))

    protected_vm_ids = set()
    for association in associations:
        if not isinstance(association, dict) or not isinstance(association.get('object_ids'), list):
            raise TaggingApiError('Tag association lookup returned an invalid response')
        logging.debug(
            'Zerto tag check: tag id=%s has %d attached objects',
            association.get('tag_id'),
            len(association['object_ids']),
        )
        for object_id in association['object_ids']:
            if not isinstance(object_id, dict):
                raise TaggingApiError('Tag association lookup returned an invalid response')
            if object_id.get('type') == 'VirtualMachine' and isinstance(object_id.get('id'), str):
                protected_vm_ids.add(object_id['id'])

    logging.debug(
        'Zerto tag check: found %d protected virtual machines: %s',
        len(protected_vm_ids),
        sorted(protected_vm_ids),
    )
    logging.debug('Zerto tag check: made %d vCenter REST API calls', rest_api_calls)
    return protected_vm_ids, rest_api_calls


def run():
    parser = cli.Parser()
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex match against vm name'))
    parser.add_optional_arguments(CheckArgument.BANNED('regex match against vm name'))
    parser.add_custom_argument(
        '--include-powered-off',
        action='store_true',
        help='include powered-off VMs in the tag compliance check',
    )
    args = parser.get_args()
    si = service_instance.connect(args)

    check = Check()

    if args.vihost:
        host = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve={'name': args.vihost},
        )
        if not host:
            raise CheckVsphereException(f"host {args.vihost} not found")
        parentView = host[0]['obj'].obj
    else:
        parentView = si.content.rootFolder

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    vms = find_entity_views(
        si,
        vim.VirtualMachine,
        begin_entity=parentView,
        properties=['name', 'config.template'],
    )
    logging.debug('Zerto tag check: discovered %d virtual machines', len(vms))

    candidates = {}
    ignored_vms = 0
    offline_vms = 0
    template_vms = 0
    for vm in vms:
        name = vm['props']['name']
        if isbanned(args, name):
            ignored_vms += 1
            logging.debug('Zerto tag check: excluding VM %s because it matches --exclude', name)
            continue
        if not isallowed(args, name):
            ignored_vms += 1
            logging.debug('Zerto tag check: excluding VM %s because it does not match --include', name)
            continue
        if vm['props'].get('config.template'):
            template_vms += 1
            logging.debug('Zerto tag check: excluding template %s', name)
            continue
        if not args.include_powered_off and vm['props'].get('runtime.powerState') != 'poweredOn':
            offline_vms += 1
            logging.debug('Zerto tag check: excluding powered-off VM %s', name)
            continue

        vm_id = vm['obj'].obj._moId
        candidates[vm_id] = name
        logging.debug('Zerto tag check: candidate VM id=%s name=%s', vm_id, name)

    logging.debug('Zerto tag check: evaluating %d eligible virtual machines', len(candidates))

    try:
        protected_vm_ids, rest_api_calls = get_protected_vm_ids(args)
    except TaggingApiError as error:
        check.exit(Status.UNKNOWN, 'Unable to query vCenter tagging API: {}'.format(error))

    if protected_vm_ids is None:
        check.exit(Status.CRITICAL, '{} category not found'.format(ZERTOTAG_CATEGORY))

    check.add_message(Status.OK, 'no VMs missing Zerto tags')
    candidate_vm_ids = set(candidates)
    tagged_vm_ids = candidate_vm_ids & protected_vm_ids
    missing_vm_ids = sorted(candidate_vm_ids - protected_vm_ids, key=lambda item: candidates[item])
    logging.debug(
        'Zerto tag check: found %d of %d eligible VMs with a Zerto tag',
        len(tagged_vm_ids),
        len(candidate_vm_ids),
    )
    logging.debug('Zerto tag check: found %d VMs without a Zerto tag', len(missing_vm_ids))
    for vm_id in missing_vm_ids:
        check.add_message(Status.CRITICAL, '{} is missing Zerto tag'.format(candidates[vm_id]))

    check.add_perfdata(label='vms', value=len(candidate_vm_ids))
    check.add_perfdata(label='tagged_vms', value=len(tagged_vm_ids))
    check.add_perfdata(label='missing_vms', value=len(missing_vm_ids))
    check.add_perfdata(label='offline_vms', value=offline_vms)
    check.add_perfdata(label='ignored_vms', value=ignored_vms)
    check.add_perfdata(label='template_vms', value=template_vms)
    check.add_perfdata(label='discovered_vms', value=len(vms))
    check.add_perfdata(label='rest_api_calls', value=rest_api_calls)

    (code, message) = check.check_messages(separator='\n')
    check.exit(
        code=code,
        message=message
    )


if __name__ == "__main__":
    run()
