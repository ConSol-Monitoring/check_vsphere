---
title: vm-tools
---

## Description

This command reports any VMs that have VMware Tools not running.
If it finds any the check result is CRITICAL.

## Options

Besides the [general options](../../general-options/) this command supports the
following options:

| options | description |
|---|---|
| `--allowed REGEX` | (optional) REGEX is checked against `<name of VirtualMachine>`, if REGEX doesn't match the vm is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of VirtualMachine>`, if REGEX does match the vm is ignored |

## Examples

``` bash
check_vsphere vm-tools -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
```
