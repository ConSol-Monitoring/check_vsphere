# perf

## Description

The perf command extracts a values from a
[_PerfCounter_](https://vdc-download.vmware.com/vmwb-repository/dcr-public/bf660c0a-f060-46e8-a94d-4b5e6ffc77ad/208bc706-e281-49b6-a0ce-b402ec19ef82/SDK/vsphere-ws/docs/ReferenceGuide/vim.PerformanceManager.html).
You can get a list of all available counters with a short description (as
provided by the API) with the [list-metrics](/cmd/list-metrics) command.

## Options

Besides the [general options](/cmd/) this command supports the following
options:

| option | description |
|---|---|
| `--vimtype VIMTYPE` | the object type to check, see [common options](/cmd/?id=common-options) |
| `--vimname VIMNAME` | name of the vimtype object, see [common options](/cmd/?id=common-options) |
| `--critical CRITICAL`   | warning threshold, see [common options](/cmd/?id=common-options) |
| `--warning WARNING`     | warning threshold, see [common options](/cmd/?id=common-options) |
| `--perfcounter PERFCOUNTER` | a colon separated string composed of groupInfo.key:nameInfo.key:rollupType |
| `--perfinstance PERFINSTANCE` | the instance of of the metric to monitor.<br/>defaults to empty string, which is not always available but means an aggregated value over all instances.<br/>Can also be `*` meaning all instances, in this case the threshold is checked against each of the instances |
| `--maintenance-state` | exit state if the host is in maintenance,<br/> one of `OK, WARNING, CRITICAL, UNKNOWN` (only has a meaning with `--vimtype HostSystem` |
| `--interval INTERVALID` | defaults to `20` which works in most cases, other possible values `300, 1800, 7200, 86400` and maybe more ...|

## Examples

```
# check for too much cpu usage
check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
  --vimtype HostSystem  --vimname esx1.int.example.com \
  --perfcounter cpu:usage:average --perfinstance '' \
  --critical 80

# check for too less cpu usage (application died?)
check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
  --vimtype HostSystem  --vimname esx1.int.example.com \
  --perfcounter cpu:usage:average \
  --critical 5:

# check if there was a reboot within the last 10 minutes
check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
  --vimtype HostSystem  --vimname esx1.int.example.com \
  --perfcounter sys:uptime:latest \
  --critical 600:

# check disk latency
$ check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vimname esx1.int.example.com --vimtype HostSystem \
	--perfcounter disk:totalLatency:average
VSPHERE-PERFCOUNTER UNKNOWN - Cannot find disk:totalLatency:average for the queried resources

# On that error you may want to try --perfinstance '*'

$ check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vimname esx1.int.example.com --vimtype HostSystem \
	--perfcounter disk:totalLatency:average --perfinstance '*'
VSPHERE-PERFCOUNTER OK - disk:totalLatency:average_naa.6000eb3810d426400000000000000277 has value 0 Millisecond
  disk:totalLatency:average_naa.600605b00ba8cb0022564867b8c8cc32 has value 2 Millisecond
  disk:totalLatency:average_naa.6000eb3810d4264000000000000000b2 has value 0 Millisecond
  disk:totalLatency:average_naa.600605b00ba8cb001fd947850523e56d has value 0 Millisecond
  disk:totalLatency:average_naa.600605b00ba8cb0029700b163217244e has value 6 Millisecond
  disk:totalLatency:average_naa.6000eb3810d4264000000000000002b3 has value 1 Millisecond
| 'disk:totalLatency:average_naa.6000eb3810d426400000000000000277'=0.0ms;;;;
'disk:totalLatency:average_naa.600605b00ba8cb0022564867b8c8cc32'=2.0ms;;;;
...

$ check_vsphere perf -s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vimname esx1.int.example.com --vimtype HostSystem \
	--perfcounter disk:totalLatency:average --perfinstance 'naa.600605b00ba8cb0022564867b8c8cc32'
```

## Rosetta

| check\_vmware\_esx | check\_vsphere | vimtypes |
|---|---|---|
| `--select cpu --subselect usage` | `perf --perfcounter cpu:usage:average`   | HostSystem, VirtualMachine |
| `--select cpu --subselect ready` | `perf --perfcounter cpu:ready:summation` | HostSystem, VirtualMachine |
| `--select cpu --subselect wait`  | `perf --perfcounter cpu:wait:summation`  | HostSystem, VirtualMachine |
| `--select mem --subselect usage` | `perf --perfcounter mem:usage:average`   | HostSystem, VirtualMachine |
| `--select mem --subselect consumed` | `perf --perfcounter mem:consumed:average`   | HostSystem, VirtualMachine |
| `--select mem --subselect swapused` | `perf --perfcounter mem:swapused:average`   | HostSystem, VirtualMachine |
| `--select mem --subselect overhead` | `perf --perfcounter mem:overhead:average`   | HostSystem, VirtualMachine |
| `--select mem --subselect memctl`   | `perf --perfcounter mem:vmmemctl:average`   | HostSystem, VirtualMachine |
| `--select io --subselect aborted` | `perf --perfcounter disk:commandsAborted:summation` | HostSystem, VirtualMachine |
| `--select io --subselect resets` | `perf --perfcounter disk:busResets:summation` | HostSystem, VirtualMachine |
| `--select io --subselect read` | `perf --perfcounter disk:read:average` | HostSystem, VirtualMachine |
| `--select io --subselect read_latency` | `perf --perfcounter disk:totalReadLatency:average` | HostSystem, VirtualMachine |
| `--select io --subselect write` | `perf --perfcounter disk:write:average` | HostSystem, VirtualMachine |
| `--select io --subselect write_latency` | `perf --perfcounter disk:totalWriteLatency:average` | HostSystem, VirtualMachine |
| `--select io --subselect usage` | `perf --perfcounter disk:usage:average` | HostSystem, VirtualMachine |
| `--select io --subselect kernel_latency` | `perf --perfcounter disk:kernelLatency:average` | HostSystem, VirtualMachine |
| `--select io --subselect device_latency` | `perf --perfcounter disk:deviceLatency:average` | HostSystem, VirtualMachine |
| `--select io --subselect queue_latency` | `perf --perfcounter disk:queueLatency:average` | HostSystem, VirtualMachine |
| `--select io --subselect total_latency` | `perf --perfcounter disk:totalLatency:average` | HostSystem, VirtualMachine |
| `--select net --subselect usage` | `perf --perfcounter net:usage:average` | HostSystem, VirtualMachine |
| `--select net --subselect receive` | `perf --perfcounter net:received:average` | HostSystem, VirtualMachine |
| `--select net --subselect send` | `perf --perfcounter net:transmitted:average` | HostSystem, VirtualMachine |
| `--select uptime` | `perf --perfcounter sys:uptime:latest` | HostSystem,VirtualMachine |
| `--select cluster --subselect effectivecpu` | `perf --perfcounter clusterservices:effectivecpu:average` | ClusterComputeResource |
| `--select cluster --subselect effectivemem` | `perf --perfcounter clusterservices:effectivemem:average` | ClusterComputeResource |
| `--select cluster --subselect failover` | `perf --perfcounter clusterservices:failover:latest` | ClusterComputeResource |
| `--select cluster --subselect cpufairness` | `perf --perfcounter clusterservices:cpufairness:latest` | ClusterComputeResource |
| `--select cluster --subselect memfairness` | `perf --perfcounter clusterservices:memfairness:latest` | ClusterComputeResource |
