# host-nic

## Description

The host-nic command checks if all nics are connected. It's basically the same
as `--select net --subselect=nic` from check\_vmware\_esx against a host.

## Options

Besides the [general options](/cmd/) this command supports the following
options:

| option | description |
|---|---|
| `--vihost HOSTNAME` | (optional) the name of the HostSystem to check, if omitted the first HostSystem found is checked, which is handy if you run this check directly against the host |
| `--maintenance-state STATE` | one of OK, WARNING, CRITICAL, UNKNOWN. The status to use when the host is in maintenance mode, this defaults to UNKNOWN except when --mode maintenance, then the default is CRITICAL |
| `--unplugged_state STATE` | one of OK, WARNING, CRITICAL. The status to use when a nic is in plugged state, defaults to WARNING |
| `--banned REGEX` | all matching nics matching this REGEXP are ignores, can be used multiple times |

## Examples

```
check_vsphere host-nic \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
        --vihost esx-2.example.com --mode status
OK: All nics connected
```
