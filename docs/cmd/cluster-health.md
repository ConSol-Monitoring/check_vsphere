---
title: cluster-health
---

## Description

The `cluster-health` command checks the health of a vSphere cluster, evaluating node status against user-defined thresholds. By default it treats nodes that are disconnected or in maintenance as faulty; you can customize what counts as a failure via `--faulty`.

## Options

Besides the [general options](../../general-options/), this command supports the following options:

| option | description |
|---|---|
| `--cluster-name CLUSTER_NAME` | Name of the cluster to check |
| `--cluster-threshold CLUSTER_THRESHOLD` | Cluster threshold: `[max_members:]warn:crit`. Numbers or percentages; `max_members` optional. |
| `--nostandby` | Standby nodes are not considered part of the cluster |
| `--faulty FAULTY` | Fault conditions to treat as failures (e.g., `*inMaintenance`, `*notconnected`, `inStandby`, `inQuarantine`, `overallStatusRed`, `overallStatusYellow`, `overallStatusGrey`). `*` marks default entries |

## --cluster-threshold details

`--cluster-threshold CLUSTER_THRESHOLD`

The syntax is `[max_members:]warn_threshold:crit_threshold`.

- `max_members` (optional) - apply the rule to clusters with up to this many members (<=). If omitted, the rule is the fallback for any larger size.
- `warn_threshold` - number or percent of faulty nodes that triggers a WARNING.
- `crit_threshold` - number or percent that triggers a CRITICAL.

Thresholds may be specified as absolute numbers (e.g., `1`) or percentages (e.g., `10%`). Mixed forms are allowed (e.g., `4:1:50%`).

You can supply several `--cluster-threshold` flags for different cluster sizes. Rules apply to clusters up to their `max_members`; if multiple rules match, the smallest `max_members` wins. Exactly one rule must omit `max_members`; that one is the fallback.

Quick examples:

- `3:1:1` - For clusters up to 3 nodes: a single fault triggers a critical state (warning and critical equal).
- `5:1:3` - For clusters up to 5 nodes: warn at >=1 faulty node, critical at >=3.
- `10:2:5` - For clusters up to 10 nodes: warn at 2 faulty nodes, critical at 5.
- `50:5:15` - For clusters up to 50 nodes: warn at 5 faulty nodes, critical at 15.
- `10%:20%` - Fallback for larger clusters: warning at 10% failures, critical at 20%.

## Examples

```bash
check_vsphere cluster-health \
  --host vcenter.example.com \
  -u naemon@vsphere.local \
  --cluster-threshold 3:1:1 \
  --cluster-threshold 5:1:3 \
  --cluster-threshold 10:2:5 \
  --cluster-threshold 50:5:15 \
  --cluster-threshold '10%:20%' \
  --cluster-name MyCluster
```