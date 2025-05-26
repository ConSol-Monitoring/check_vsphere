---
title: vm-guestfs
---

## Description

This command can check disk usage of mounted filesystems in a
VM if vmwaretools are running.

## Options

Besides the [general options](../../general-options/) this command supports the
following options:

| options | description |
|---|---|
| `--vm-name VMNAME` | name of the VM to check |
| `--warning THRESHOLD` | (optional) critical threshold, see [common options](../../general-options/#common-options) |
| `--critical THRESHOLD` | (optional) critical threshold, see [common options](../../general-options/#common-options) |
| `--allowed REGEX` | (optional) REGEX is checked against `<path of mountpoint>`, if REGEX doesn't match the fs is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<path of mountpoint>`, if REGEX does match the fs is ignored |
| `--match-method [search,match,fullmatch]` | see [common options](../../general-options/#common-options) |
| `--metric METRIC`     | the name of the metric to check, can be one of `usage`, `used`, `free`. <br>`used` and `free` can be suffixed by a unit (B, kB, MB, GB), like `free_MB` or `used_GB`. <br>if omitted it defaults to `usage`, which is (100 * used/capacity) |


## Examples

``` bash
# check all filesystems mounted under /var (/var /var/tmp /var/log etc)
# if they have less than 5GB of free space
check_vsphere vm-guestfs -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --vm-name examplevm \
  --metric free_GB \
  --critical 5: \
  --match-method match \
  --allow /var
```
