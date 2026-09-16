---
title: zertotag
---

## Description

This command verifies that eligible virtual machines have a tag in a vCenter
category named `Zerto - Protection Automation`. The hyphen may also be an en
dash (`U+2013`) to support the category name used by Zerto DRaaS protection
automation.

The command reports CRITICAL for every eligible VM without a tag in that
category. It also reports CRITICAL when the required category does not exist.
Tagging API, authentication, permission, and connection failures are reported
as UNKNOWN.

The vCenter account needs permission to list tagging categories, tags, and tag
associations.

The command exports the following performance data:

| label | description |
|---|---|
| `discovered_vms` | VMs discovered in the selected vCenter or `--vihost` scope. |
| `vms` | Eligible VMs evaluated for tag compliance. |
| `tagged_vms` | Eligible VMs with a matching tag. |
| `missing_vms` | Eligible VMs without a matching tag. |
| `offline_vms` | Powered-off non-template VMs excluded by default. |
| `ignored_vms` | VMs excluded by `--include` or `--exclude`. |
| `template_vms` | Templates excluded from the check. |
| `rest_api_calls` | vCenter REST requests, including authentication. |

## Options

Besides the [general options](../../general-options/), this command supports
the following options:

| options | description |
|---|---|
| `--vihost VIHOST` | Only check VMs on this ESXi host. If omitted, check all known VMs. |
| `--include REGEX` | Only check VMs whose names match this regular expression. May be provided more than once. |
| `--exclude REGEX` | Do not check VMs whose names match this regular expression. May be provided more than once. |
| `--include-powered-off` | Include powered-off VMs. Powered-off VMs are excluded by default. |

Templates are always excluded. The selected `--port` and SSL verification
settings are used for both the SOAP inventory query and vCenter tagging API.

## Examples

```bash
check_vsphere zertotag -nossl \
  -s vcenter.example.com \
  -u naemon@vsphere.local \
  --include-powered-off
```
