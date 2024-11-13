---
title: vm-tools
---

## Description

This command reports any VMs that have VMware Tools not running.
If it finds any the check result is CRITICAL.

## Options

[general options](../../general-options/) 

## Examples

``` bash
check_vsphere vm-tools -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
```
