---
title: power-state
---

## Description

This command checks the power state of all hosts in vCenter.

## Options

Besides the [general options](../../general-options/), this command supports the following
options:

| options | description |
|---|---|
| `--allowed REGEX` | (optional) REGEX is checked against `<name of HostSystem>`, if REGEX doesn't match the host is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of HostSystem>`, if REGEX does match the host is ignored |
| `--cluster-name CLUSTERNAME` | (optional) consider only hosts in cluster CLUSTERNAME |
| `--metric METRIC` | One of total, up, down, ignored, up%, down% | which metric to apply THRESHOLD on (default is `down`) |
| `--warning THRESHOLD` | (optional) warning threshold, see [common options](../../general-options/#common-options) |
| `--critical THRESHOLD` | (optional) critical threshold, see [common options](../../general-options/#common-options) |

If no thresholds are given, the check behaves like
`power-state --critical 1 --metric down`, but the output differs slightly.

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
