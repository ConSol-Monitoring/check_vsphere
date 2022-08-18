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

    WARNING_THRESHOLD = {
        'name_or_flags': ['--warning'],
        'options': {'action': 'store', 'help': 'warning threshold'},
    }
    CRITICAL_THRESHOLD = {
        'name_or_flags': ['--critical'],
        'options': {'action': 'store', 'help': 'critical threshold'},
    }
    def ALLOWED(help):
        return {
            'name_or_flags': ['--allowed'],
            'options': {
                'default': [],
                'help': help,
                'action': 'append',
            }
        }
    def BANNED(help):
        return {
            'name_or_flags': ['--banned'],
            'options': {
                'default': [],
                'help': help,
                'action': 'append',
            }
        }

def isbanned(args, name):
    '''
    checks name against regexes in args.banned
    '''
    if args.banned:
        for pattern in args.banned:
            p = re.compile(pattern)
            if p.search(name):
                return True

    return False

def isallowed(args, name):
    '''
    checks name against regexes in args.allowed
    '''
    if args.allowed:
        for pattern in args.allowed:
            p = re.compile(pattern)
            if p.search(name):
                return True
        return False

    return True
