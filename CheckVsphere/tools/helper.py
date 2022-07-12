import re
from pyVmomi import vim, vmodl

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
        if obj.name == name: # TODO: maybe make this case insensitive?
            return obj

    return None

def find_entity_views(service_instance, view_type, begin_entity=None, sieve=None, properties=None):
    assert service_instance is not None
    assert view_type is not None
    if not begin_entity:
        begin_entity = service_instance.content.rootFolder
    if not sieve:
        sieve = dict()
    if not properties:
        properties = []
    assert isinstance(sieve, dict)
    assert isinstance(properties, list)

    propertySpec = vmodl.query.PropertyCollector.PropertySpec(
        pathSet=list(sieve.keys()),
        type=view_type,
        all=False
    )

    property_filter_spec = get_search_filter_spec(begin_entity, [propertySpec])
    obj_contents = service_instance.content.propertyCollector.RetrieveContents([property_filter_spec])

    for obj in obj_contents:
        print(obj)


def get_search_filter_spec(begin_entity, property_specs):
    # What's wrong with you VMWARE?
    TraversalSpec = vmodl.query.PropertyCollector.TraversalSpec
    SelectionSpec = vmodl.query.PropertyCollector.SelectionSpec
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
    FilterSpec = vmodl.query.PropertyCollector.FilterSpec

    resourcePoolTraversalSpec = TraversalSpec(
        name='resourcePoolTraversalSpec',
        type=vim.ResourcePool,
        path='resourcePool',
        skip=False,
        selectSet=[
            SelectionSpec(name='resourcePoolTraversalSpec'),
            SelectionSpec(name='resourcePoolVmTraversalSpec')
        ],
    )

    resourcePoolVmTraversalSpec = TraversalSpec(
        name='resourcePoolVmTraversalSpec',
        type=vim.ResourcePool,
        path='vm',
        skip=False,
    )

    computeResourceRpTraversalSpec = TraversalSpec(
        name='computeResourceRpTraversalSpec',
        type=vim.ComputeResource,
        path='resourcePool',
        skip=False,
        selectSet=[
            SelectionSpec(name='resourcePoolTraversalSpec'),
            SelectionSpec(name='resourcePoolVmTraversalSpec')
        ],
    )

    computeResourceHostTraversalSpec = TraversalSpec(
        name='computeResourceHostTraversalSpec',
        type=vim.ComputeResource,
        path='host',
        skip=False,
    )

    datacenterHostTraversalSpec = TraversalSpec(
        name='datacenterHostTraversalSpec',
        type=vim.Datacenter,
        path='hostFolder',
        skip=False,
        selectSet=[
            SelectionSpec(name='folderTraversalSpec'),
        ],
    )

    datacenterVmTraversalSpec = TraversalSpec(
        name='datacenterVmTraversalSpec',
        type=vim.Datacenter,
        path='vmFolder',
        skip=False,
        selectSet=[
            SelectionSpec(name='folderTraversalSpec'),
        ],
    )

    hostVmTraversalSpec = TraversalSpec(
        name='hostVmTraversalSpec',
        type=vim.HostSystem,
        path='vm',
        skip=False,
        selectSet=[
            SelectionSpec(name='folderTraversalSpec'),
        ],
    )

    folderTraversalSpec = TraversalSpec(
        name='folderTraversalSpec',
        type=vim.Folder,
        path='childEntity',
        skip=False,
        selectSet=[
            SelectionSpec(name='folderTraversalSpec'),
            SelectionSpec(name='datacenterHostTraversalSpec'),
            SelectionSpec(name='datacenterVmTraversalSpec'),
            SelectionSpec(name='computeResourceRpTraversalSpec'),
            SelectionSpec(name='computeResourceHostTraversalSpec'),
            SelectionSpec(name='hostVmTraversalSpec'),
            SelectionSpec(name='resourcePoolVmTraversalSpec'),
        ],
    )

    obj_spec = ObjectSpec(
        obj=begin_entity,
        skip=False,
        selectSet=[
            folderTraversalSpec,
            datacenterVmTraversalSpec,
            datacenterHostTraversalSpec,
            computeResourceHostTraversalSpec,
            computeResourceRpTraversalSpec,
            resourcePoolTraversalSpec,
            hostVmTraversalSpec,
            resourcePoolVmTraversalSpec
        ]
    )

    return FilterSpec(
        propSet=property_specs,
        objectSet=[ obj_spec ],
    )


def get_metric(perfMgr, perfCounterStr, perfInstance):
    for counter in perfMgr.perfCounter:
        if f'{counter.groupInfo.key}:{counter.nameInfo.key}:{counter.rollupType}' == perfCounterStr:
            return ( counter, vim.PerformanceManager.MetricId(
                counterId = counter.key,
                instance = perfInstance
            ))
    return (None, None)
