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
    assert isinstance(sieve, dict)

    propertySpec = vmodl.query.PropertyCollector.PropertySpec(
        pathSet=list(sieve.keys()),
        type=view_type,
        all=False
    )

    property_filter_spec = get_search_filter_spec(view_type, begin_entity, [propertySpec])
    obj_contents = service_instance.content.propertyCollector.RetrieveContents([property_filter_spec])


def get_search_filter_spec(view_type, begin_entity, property_specs):
    TraversalSpec = vmodl.query.PropertyCollector.TraversalSpec
    SelectionSpec = vmodl.query.PropertyCollector.SelectionSpec
    ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec

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

    return vmodl.query.PropertyCollector.FilterSpec(
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

def get_key_metrics(perfMgr, group, names):
    """
    Find MetricIds by metric group and metric names
    Look at generic_performance_values() for details
    """
    metrics = {}
    for counter in perfMgr.perfCounter:
        if counter.groupInfo.key == group:
            cur_name = f'{counter.nameInfo.key}.{counter.rollupType}'
            for n in names:
                if n.startswith(cur_name):
                    match = re.match(r'^(\w+)\.(\w+)(?::(.*))?', n)
                    metrics[counter.key] = (
                        n,
                        vim.PerformanceManager.MetricId(
                            counterId = counter.key,
                            instance = (match.groups()[2] or "")
                        )
                    )
    return metrics

def generic_performance_values(si, views, group, names):
    """
    Fetch Perfromance values from objects by group and names

    views: this is a list of obj from which we want the perf values
           for example a list of vim.HostSystem

    group: the name of the metric group we are interested in, like "disk" or "cpu"
           TODO: find a documentation where all possible values are listed

    names: List of metric names. The name is generated like
           f'{ c.nameInfo.key }.{c.rollupType}:{instance}'
    """
    perfMgr = si.content.perfManager
    metrics = get_key_metrics(perfMgr, group, names)
    perfQuerySpec = []

    for v in views:
        perfQuerySpec.append(
            vim.PerformanceManager.QuerySpec(
                maxSample=1,
                entity=v,
                metricId=[ x[1] for x in metrics.values() ],
                intervalId=20,
            )
        )

    perfData = perfMgr.QueryPerf(querySpec=perfQuerySpec)

    values = []

    for p in perfData:
        vals = {}
        for n in names:
            vals[n] = None
        for v in p.value:
            vals[metrics[v.id.counterId][0]] = v
        values.append(vals)

    return values
