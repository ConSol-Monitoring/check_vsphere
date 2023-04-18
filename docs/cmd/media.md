---
title: media
---

## Description

This command reports any VMs that have floppies or cdroms attached. If it finds
any the check result is CRITICAL.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| options | description |
|---|---|
| `--vihost VIHOST` | (optional) see [common options](../../general-options/#common-options),<br/> only check vms on this host. If omitted all known VMs are checked |


## Examples

``` bash
check_vsphere media -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --vihost esx1.int.example.com
```
