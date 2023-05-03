# host-service

## Description

The host-service checks the services are running. Since you probably don't have
all of them running you probably want to filter the ones to check with the
`--allowed` parameter.

## Options

Besides the [general options](/cmd/) this command supports the following
options:

| option | description |
|---|---|
| `--vihost HOSTNAME` | (optional) the name of the HostSystem to check, if omitted the first HostSystem found is checked, which is handy if you run this check directly against the host |
| `--maintenance-state STATE` | one of OK, WARNING, CRITICAL, UNKNOWN. The status to use when the host is in maintenance mode, this defaults to UNKNOWN |
| `--allowed REGEX` | (optional) REGEX is checked against `<name of service>`, if REGEX doesn't match the service is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of datastore>`, if REGEX does match the service is ignored |


## Examples

```
$ check_vsphere host-services \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
        --vihost esx-2.example.com --allowed 'vpxa|ntpd|DCUI'
OK: running: 3; not running: 0
DCUI running
ntpd running
vpxa running
```

```
$ check_vsphere host-services \
	-s vcenter.example.com -u naemon@vsphere.local -nossl \
        --vihost esx-2.example.com --allowed 'snmpd'
CRITICAL: running: 3; not running: 1
snmpd not running
DCUI running
ntpd running
vpxa running
```
