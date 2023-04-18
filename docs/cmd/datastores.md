---
title: datastores
---

## Description

This command checks remaining capacity on the datastores, and if they are
accessible.  This is known as `--select volumes` from check\_vmware\_esx.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| options | description |
|---|---|
| `--allowed REGEX` | (optional) REGEX is checked against `<name of datastore>`, if REGEX doesn't match the snapshot is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of datastore>`, if REGEX does match the snapshot is ignored |
| `--vimtype VIMTYPE` | the object type to check, see [common options](../../general-options/#common-options), currently HostSystem and ClusterComputeResource are supported here, if omitted all datastores are checked |
| `--vimname VIMNAME` | name of the vimtype object, see [common options](../../general-options/#common-options) |
| `--critical CRITICAL`   | critical threshold, see [common options](../../general-options/#common-options) |
| `--warning WARNING`     | warning threshold, see [common options](../../general-options/#common-options) |
| `--metric METRIC`     | the name of the metric to check, can be one of `usage`, `used`, `free`. <br>`used` and `free` can be suffixed by a unit (B, kB, MB, GB), like `free_MB` or `used_GB`. <br>if omitted it defaults to `usage`, which is (100 * used/capacity) |

In case of `--vimtype HostSystem` it may be useful to omit the `--vimname` when
you run this command directly against the HostSystem (not through the vcenter).

## Examples

``` bash
# notifiy volumes that have less than 10GB left
check_vsphere datastores -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --metric free_GB \
  --critical 10: \
  --vimtype HostSystem \
  --vimname esx1.example.com
```

``` bash
# notifiy volumes that have a usage of 90%
check_vsphere datastores -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --critical 90
```
