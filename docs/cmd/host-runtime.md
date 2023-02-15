# host-runtime

## Description

The host-runtime provides various checks against a hosts runtime. It's basically
the same as `--select runtime` from check\_vmware\_esx against a host.

## Options

Besides the [general options](/cmd/) this command supports the following
options:

| option | description |
|---|---|
| `--vihost HOSTNAME` | the name of the HostSystem to check |
| `--mode MODE` | what to check to perform, one of `con`, `health`, `issues`, `status`, `temp`, `version`, `maintenance` |
| `--maintenance-state STATE` | one of OK, WARNING, CRITICAL, UNKNOWN. The status to use when the host is in maintenance mode, this defaults to UNKKNOWN except when --mode maintenance, then the default is CRITICAL |

## Examples

```
check_vsphere host-runtime \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
        --vihost esx-2.example.com --mode status
VSPHERE-RUNTIME CRITICAL - overall status is RED
```

```
check_vsphere host-runtime \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vihost esx-2.example.com --mode con
VSPHERE-RUNTIME OK - connection state is 'connected'
```

```
check_vsphere host-runtime \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vihost esx-2.example.com --mode health
VSPHERE-RUNTIME OK - All 53 health checks are GREEN: memory: 10, storage: 9, other: 1, voltage: 12, fan: 4, temperature: 15, power: 2
```

```
check_vsphere host-runtime \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vihost esx-2.example.com --mode status
VSPHERE-RUNTIME CRITICAL - overall status is RED
```

```
check_vsphere host-runtime \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
	--vihost esx-2.example.com --mode temp
VSPHERE-RUNTIME OK - All temperature sensors green
| 'Memory Device 77 DIMMD2'=43.0;;;; ...
```
