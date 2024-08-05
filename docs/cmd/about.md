---
title: about
---

### Description

This command just uses the [general options](../../general-options/). It connects to the
API and prints some vsphere version information.

### Options

Besides the [general options](../../general-options/) this command supports the following
options:

| option | description |
|---|---|
|`--skip-permission` | skips the System.View permission check, if omitted about check if it has System.View permissions. If it does not and `--sessionfile` is active the sessionfile is deleted if the check fails. |


### Example

```
$ check_vsphere about -s vcenter.example.com -u naemon@vsphere.local -nossl
OK: VMware vCenter Server 6.7.0 build-18485185, api: VirtualCenter/6.7.3, product: VMware VirtualCenter Server 6.0
```
