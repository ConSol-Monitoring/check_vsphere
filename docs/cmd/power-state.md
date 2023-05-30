---
title: power-state
---

## Description

This command checks the powerState of all hosts in a vcenter. If every host is in state powerOn exit code is `0` otherwise `2`.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| options | description |
|---|---|
| `--allowed REGEX` | (optional) REGEX is checked against `<name of HostSystem>`, if REGEX doesn't match the host is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of HostSystem>`, if REGEX does match the host is ignored |

## Examples

```
$ check_vsphere power-state \
  -s vcenter.example.com \
  -u naemon@vsphere.local
OK: 10 hosts, 0 ignored, unpowered 0
All hosts ok
| 'hosts'=10.0;;;;
'ignored hosts'=0.0;;;;
'hosts with power'=10.0;;;;
'monplugin_time'=0.058525s
```
