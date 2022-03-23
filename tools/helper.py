import re
from pyVmomi import vim

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
