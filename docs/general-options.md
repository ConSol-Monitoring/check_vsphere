---
title: General Options
weight: 100
---

| option | description |
|---|---|
| `-s HOST, --host HOST`  | vSphere service address to connect to |
| `-o PORT, --port PORT`  | Port to connect on |
| `-u USER, --user USER`  | User name to use when connecting to host |
| `-p PASSWORD, --password` | Password to use when connecting to host, can also be set by env `VSPHERE_PASS` |
| `-nossl, --disable-ssl-verification` | Disable ssl host certificate verification |
| `--sessionfile FILE` | **EXPERIMENTAL** it caches session information in FILE to avoid logging in and out so much, it messes around with internals of the pyVmomi library, so it is marked as experimental and probably stay so until they provide some public API for this use case (which is already in their master branch ...) |

# Common Options

| option | description |
|---|---|
| `--vihost VIHOST`   | name of the ESXi Host as seen by the vCenter |
| `--vimtype VIMTYPE` | the object type to check,<br/>it's a [managed entity](https://dp-downloads.broadcom.com/api-content/apis/API_VWSA_001/8.0U3/html/ReferenceGuides/vim.ManagedEntity.html) like: HostSystem, Datacenter or VirtualMachine |
| `--vimname VIMNAME` | the name of the ManagedEntity of vimtype  |
| `--warning WARNING`     | warning [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |
| `--critical CRITICAL`   | critical [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |

# Environment Variables

| var | description |
|---|---|
| `CONNECT_NOFAIL` | if set a connection error exits with status OK |
| `TIMEOUT` | Global timeout of the plugin in seconds, defaults to `30` |
| `VSPHERE_PASS` | default value for `--password` option |
