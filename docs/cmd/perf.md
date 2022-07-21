# perf

## Description

The perf command extracts a values from a
[_PerfCounter_](https://vdc-repo.vmware.com/vmwb-repository/dcr-public/1ef6c336-7bef-477d-b9bb-caa1767d7e30/82521f49-9d9a-42b7-b19b-9e6cd9b30db1/vim.PerformanceManager.html).
You can get a list of all available counters with a short description (as
provided by the API) with the [listmetrics](/cmd/listmetrics) command.

## Options

Besides the [general options](/cmd/) this command supports the following
options:

| options | description |
|---|---|
| `--vimtype VIMTYPE` | the object type to check, see [common options](/cmd/?id=common-options) |
| `--vimname VIMNAME` | name of the vimtype object, see [common options](/cmd/?id=common-options) |
| `--critical CRITICAL`   | warning threshold, see [common options](/cmd/?id=common-options) |
| `--warning WARNING`     | warning threshold, see [common options](/cmd/?id=common-options) |
| `--perfcounter PERFCOUNTER` | a colon separated string composed of groupInfo.key:nameInfo.key:rollupType |
| `--perfinstance PERFINSTANCE` | the instance of of the metric to monitor.<br/>defaults to empty string, which is not always available but means an aggregated value over all instances.<br/>Can also be `*` meaning all instances, in this case the threshold is checked against each of the instances |

## Examples

``` bash
check_vmware perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
  --vimtype HostSystem  --vimname esx1.int.example.com \
  --perfcounter cpu:usage:average --perfinstance '' \
  --critical 80
```


## Rosetta

| check\_vmware\_esx | check\_vsphere |
|---|---|
| `--select cpu --subselect usage` | `perf --perfcounter cpu:usage:average`   |
| `--select cpu --subselect ready` | `perf --perfcounter cpu:ready:summation` |
| `--select cpu --subselect wait`  | `perf --perfcounter cpu:wait:summation`  |
| `--select mem --subselect usage` | `perf --perfcounter mem:usage:average`   |
| `--select mem --subselect consumed` | `perf --perfcounter mem:consumed:average`   |
| `--select mem --subselect swapused` | `perf --perfcounter mem:swapused:average`   |
| `--select mem --subselect overhead` | `perf --perfcounter mem:overhead:average`   |
| `--select mem --subselect memctl`   | `perf --perfcounter mem:vmmemctl:average`   |
