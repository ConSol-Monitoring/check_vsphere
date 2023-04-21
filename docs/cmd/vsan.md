---
title: vsan
---

## Description

The vsan command provides checks against the vSAN system of a vcenter. Host
endpoints are currently not supported.

## Requirements

Unfortunately the [vSAN API](https://developer.vmware.com/web/sdk/8.0/vsan-python)
is not available as open source. So there is manual intervention needed to get
it working.

1. Download the [vSAN API SDK](https://developer.vmware.com/web/sdk/8.0/vsan-python)
   for python. You need a VMware account to do this.
1. install defusedxml, i.e.:
   `pip install defusedxml`
1. Copy the files `bindings/vsanmgmtObjects.py` and `samples/vsanapiutils.py`
   somehwere where your python can find it.
   For example: `python3 -m site --user-site`

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| option | description |
|---|---|
| `--vihost HOSTNAME` | (optional) the name of the HostSystem to check, if omitted the first HostSystem found is checked, which is handy if you run this check directly against the host |
| `--maintenance-state STATE` | one of OK, WARNING, CRITICAL, UNKNOWN. The status to use when the host is in maintenance mode, this defaults to UNKNOWN |
| `--mode MODE` | one of objecthealth, healthtest |
| `--include REGEX` | (optional) REGEX is checked against the cluster name |
| `--exclude REGEX` | (optional) REGEX is checked against the cluster name |
| `--include-group REGEX` | (optional) only with `--mode healthtest`, REGEX is checked against the tests' group name |
| `--include-test REGEX`  | (optional) only with `--mode healthtest`, REGEX is checked against the test name |
| `--exclude-group REGEX` | (optional) only with `--mode healthtest`, REGEX is checked against the tests' group name |
| `--exclude-test REGEX`  | (optional) only with `--mode healthtest`, REGEX is checked against the test name |
| `--cache`  | fetch cached data from the API when available and not outdated |
| `--verbose` | show also tests the where OK |

### `--mode healthtest`

This corresponds to the following in the vcenter:

If you navigate to Cluster/Monitor/vSAN/Skyline Health you will see a sidebar
with items like "Hardware compatibility", "Online Health" and so on. These are
the several group of tests (you can ignore a whole groups with
`--exclude-group/--include-group`)

You can expand them and see the individual names of each test. These can be
ignored as well (`--exclude-test/--include-test`).

### `--mode objecthealth`

REGEX of `--include`, `--exclude` is matched against cluster name.

This is an in depth check of the "vSAN object health" test. It's not very well
tested yet.

## Examples

```
$ check_vsphere vsan \
    -s vcenter.example.com -u naemon@vsphere.local \
    -m healthtest --include 'Cluster 1'
```
