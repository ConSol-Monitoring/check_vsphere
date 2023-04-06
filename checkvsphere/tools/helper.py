
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

import re
from pyVmomi import vim, vmodl
from . import serviceutil


# TODO: this might be slow, probably speed this up with
def get_obj_by_name(si, vimtype, name):
    """
    ex: get_obj_by_name(serviceinstance, vim.HostSystem, "foo.example.com")
    """
    view = si.content.viewManager.CreateContainerView(
        si.content.rootFolder,
        [vimtype],
        True
    )
    for obj in view.view:
        if obj.name == name:  # TODO: maybe make this case insensitive?
            return obj

    return None

def find_entity_views(service_instance, view_type, begin_entity=None, sieve=None, properties=None):
    """
    find_entity_views(si, vim.HostSystem, sieve={"name": "esx1.vsphere.example.com"})
    """
    assert service_instance is not None
    assert view_type is not None
    if not begin_entity:
        begin_entity = service_instance.content.rootFolder
    if not sieve:
        sieve = dict()
    if not properties:
        properties = []
    if view_type == vim.HostSystem:
        properties += ['runtime.inMaintenanceMode', 'runtime.powerState']
    if view_type == vim.VirtualMachine:
        properties += ['runtime.powerState']
    assert isinstance(sieve, dict)
    assert isinstance(properties, list)

    propertySpec = vmodl.query.PropertyCollector.PropertySpec(
        pathSet=list(sieve.keys()) + properties,
        type=view_type,
        all=False
    )

    property_filter_spec = get_search_filter_spec(begin_entity, [propertySpec])
    obj_contents = service_instance.content.propertyCollector.RetrieveContents([property_filter_spec])

    filtered_objs = []

    for obj in obj_contents:
        props = {}
        for p in obj.propSet:
            props[p.name] = p.val

        if not sieve:
            filtered_objs.append({"obj": obj, "props": props})
            continue
        else:  # FIXME: implement sieve here, currently it only works with one search pattern

            matched = True

            try:
                for property_name, property_value in sieve.items():
                    #print((property_name, property_value, props))
                    if property_name in props:
                        if props[property_name] != property_value:
                            raise Exception("Not Matched")
            except:
                matched = False

            if matched:
                filtered_objs.append({"obj": obj, "props": props})

    return filtered_objs
    # return service_instance.content.viewManager.CreateListView( obj = filtered_objs )


def get_search_filter_spec(begin_entity, property_specs):
    # What's wrong with you VMWARE?
    fullspec = serviceutil.build_full_traversal()
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    FilterSpec = vmodl.query.PropertyCollector.FilterSpec

    obj_spec = ObjectSpec(
        obj=begin_entity,
        skip=False,
        selectSet=fullspec
    )

    return FilterSpec(
        propSet=property_specs,
        objectSet=[obj_spec],
    )


def get_metric(perfMgr, perfCounterStr, perfInstance):
    for counter in perfMgr.perfCounter:
        if f'{counter.groupInfo.key}:{counter.nameInfo.key}:{counter.rollupType}' == perfCounterStr:
            return (counter, vim.PerformanceManager.MetricId(
                counterId=counter.key,
                instance=perfInstance
            ))
    return (None, None)


class CheckArgument:
    def __init__(self):
        pass

    VIMNAME = {
        'name_or_flags': ['--vimname'],
        'options': {'action': 'store', 'help': 'name of the vimtype object'},
    }

    VIMTYPE = {
        'name_or_flags': ['--vimtype'],
        'options': {
            'action': 'store',
            'help': 'the object type to check, i.e. HostSystem, Datacenter or VirtualMachine',
        },
    }

    WARNING_THRESHOLD = {
        'name_or_flags': ['--warning'],
        'options': {'action': 'store', 'help': 'warning threshold'},
    }

    CRITICAL_THRESHOLD = {
        'name_or_flags': ['--critical'],
        'options': {'action': 'store', 'help': 'critical threshold'},
    }

    def ALLOWED(help, name=None):
        if not name:
            name = ['--allowed', '--include']
        return {
            'name_or_flags': name,
            'options': {
                'default': [],
                'help': help,
                'action': 'append',
            }
        }
    def BANNED(help, name=None):
        if not name:
            name = ['--banned', '--exclude']
        return {
            'name_or_flags': name,
            'options': {
                'default': [],
                'help': help,
                'action': 'append',
            }
        }


def isbanned(args, name, attr='banned'):
    '''
    checks name against regexes in args.banned
    '''
    banned = getattr(args, attr, None)
    if banned:
        for pattern in banned:
            p = re.compile(pattern)
            if p.search(name):
                return True

    return False

def isallowed(args, name, attr='allowed'):
    '''
    checks name against regexes in args.allowed
    '''
    allowed = getattr(args, attr, None)
    if allowed:
        for pattern in allowed:
            p = re.compile(pattern)
            if p.search(name):
                return True
        return False

    return True

def process_retrieve_content(content):
    """
    reorganize RetrieveContents shit, so we can use it.
    """
    objs = []
    for o in content:
        d = {}
        d['moref'] = o.obj
        for prop in o.propSet:
            d[prop.name] = prop.val
        objs.append(d)
    return objs
