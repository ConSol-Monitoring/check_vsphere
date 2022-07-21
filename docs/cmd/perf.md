# perf

## Options

Besides the [general options][/cmd/] this command supports the following
options:

| options | description |
|---|---|
| `--vimtype VIMTYPE` | the object type to check, i.e. HostSystem, Datacenter or VirtualMachine |
| `--vimname VIMNAME` | name of the vimtype object |
| `--perfcounter PERFCOUNTER` | a colon separated string composed of groupInfo.key:nameInfo.key:rollupType |
| `--perfinstance PERFINSTANCE` | the instance of of the metric to monitor.<br/>defaults to empty string, which is not always available but means an aggregated value over all instances.<br/>Can also be `*` meaning all instances, in this case the threshold is checked against each of the instances |
|  `--critical CRITICAL`   | critical [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |
|  `--warning WARNING`     | warning [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |

## Examples

``` bash
check_vmware perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
  --vimtype HostSystem  --vimname esx1.int.example.com \
  --perfcounter cpu:usage:average --perfinstance '' \
  --critical 80
```


## Rosetta

| check_vmware_esx | check_vsphere |
|---|---|
| `--select cpu --subselect usage` | `perf --perfcounter cpu:usage:average`   |
| `--select cpu --subselect ready` | `perf --perfcounter cpu:ready:summation` |
| `--select cpu --subselect wait`  | `perf --perfcounter cpu:wait:summation`  |
| `--select mem --subselect usage` | `perf --perfcounter mem:usage:average`   |
| `--select mem --subselect consumed` | `perf --perfcounter mem:consumed:average`   |
| `--select mem --subselect swapused` | `perf --perfcounter mem:swapused:average`   |
| `--select mem --subselect overhead` | `perf --perfcounter mem:overhead:average`   |
| `--select mem --subselect memctl`   | `perf --perfcounter mem:vmmemctl:average`   |
