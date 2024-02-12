---
title: vm-net-dev
---

## Description

This command check networkdevices of vms.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| options | description |
|---|---|
| `--mode {start-unconnected}` | check for vms that have network cards configured that are not connected on startup. `--exclude` and `--include` match against a string like "vmname;Network adapter 1" |
| `--allowed REGEX` | (optional) REGEX matched against string specified in `--mode` |
| `--banned REGEX` | (optional) REGEX is matched against string specified in `--mode` |


## Examples

``` bash
check_vsphere vm-net-dev -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --mode start-unconnected
```
