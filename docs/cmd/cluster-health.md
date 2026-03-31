---
title: cluster-health
---

## Description

The `cluster-health` command checks the health of a vSphere cluster, evaluating node status against user‑defined thresholds.

## Options

Besides the [general options](../../general-options/) this command supports the following options:

| option | description |
|---|---|
| `--cluster-name CLUSTER_NAME` | Name of the cluster to check |
| `--cluster-threshold CLUSTER_THRESHOLD` | Cluster threshold: `[max_members:]warn:crit`. Numbers or percentages; max_members optional. |
| `--nostandby` | Standby nodes are not considered part of the cluster |
| `--faulty FAULTY` | Fault conditions to treat as failures (e.g., `*inMaintenance`, `*notconnected`, `inStandby`, `inQuarantine`, `overallStatusRed`, `overallStatusYellow`, `overallStatusGrey`). `*` marks default entries |

## --cluster-threshold details

`--cluster-threshold CLUSTER_THRESHOLD`

The syntax is `[max_members:]warn_threshold:crit_threshold`.

- `max_members` (optional) – applies the rule only when the cluster has this many nodes; if omitted it serves as a fallback for any size.
- `warn_threshold` – number or percentage of faulty nodes that triggers a **WARNING**.
- `crit_threshold` – number or percentage of faulty nodes that triggers a **CRITICAL**.

Thresholds can be absolute numbers (e.g., `1`) or percentages (e.g., `30%`). Mixed forms are allowed (e.g., `4:1:3`). Multiple `--cluster-threshold` flags may be given for different cluster sizes. Exactly one `--cluster-threshold` must omit `max_members` and acts as a fallback for any cluster size.

Examples:

- `1:1:1` – a 1‑node cluster is critical if any node fails.
- `4:1:3` – a 4‑node cluster warns at 1 faulty node, critical at 3.
- `30%:50%` – for clusters larger than 4 nodes, warn at ≥30 % failures, critical at ≥50 % failures.

## Examples

```bash
check_vsphere cluster-health \
  --host vcenter.example.com \
  -nossl \
  -u naemon@vsphere.local \
  -p "PW" \
  --cluster-threshold '1:1:1' \
  --cluster-threshold '4:1:3' \
  --cluster-threshold '30%:50%' \
  --cluster-name CLUSTERNAME
```
