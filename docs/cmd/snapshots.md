---
title: snapshots
---

## Description

This command checks VirtualMachine snapshots by age or count.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| options | description |
|---|---|
| `--mode {age,count}` | (required) thresholds checked against the `age` of a snapshot or against the `count` of the snapshots by VirtualMachine |
| `--allowed REGEX` | (optional) REGEX is checked against `<name of VirtualMachine>;<name of snapshot>`, if REGEX doesn't match the snapshot is ignored |
| `--banned REGEX` | (optional) REGEX is checked against `<name of VirtualMachine>;<name of snapshot>`, if REGEX does match the snapshot is ignored |
| `--critical CRITICAL`   | critical threshold, see [common options](../../general-options/#common-options) |
| `--warning WARNING`     | warning threshold, see [common options](../../general-options/#common-options) |


## Examples

``` bash
# notify if snapshots are too old
check_vsphere snapshots -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --mode age \
  --warning 150 \
  --critical 180 \
```
