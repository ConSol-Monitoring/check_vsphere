---
title: host-storage
---

## Description

The host-storage command provides various checks against a hosts storage system.
It's basically the same as `--select storage` from check\_vmware\_esx against a
host.

## Options

Besides the [general options](../../general-options/) this command supports the following
options:

| option | description |
|---|---|
| `--vihost HOSTNAME` | (optional) the name of the HostSystem to check, if omitted the first HostSystem found is checked, which is handy if you run this check directly against the host |
| `--maintenance-state STATE` | one of OK, WARNING, CRITICAL, UNKNOWN. The status to use when the host is in maintenance mode, this defaults to UNKNOWN |
| `--mode MODE` | one of adapter, lun |
| `--allowed REGEX` | (optional) REGEX is checked against a name depending on the `--mode` |
| `--banned REGEX` | (optional) REGEX is checked against a name depending on the `--mode` |

On `--mode adapter` REGEX is matched against device name, the model or the device-key of the adapter.
On `--mode lun` REGEX is matched against displayName of the scsi device

## Examples

```
$ check_vsphere host-storage  -u naemon@vsphere.local  -s vcenter.example.com  --vihost esx-1.example.com
VSPHERE-STORAGE OK - LUNs: 12; ok: 12
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae650000000000000116) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b0) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b2) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b4) state: ok
OK LUN:000 AVAGO Serial Attached SCSI Disk (naa.600605b00ba8d09022672ce36caf54d0) state: ok
OK LUN:000 AVAGO Serial Attached SCSI Disk (naa.600605b00ba8d090203f049d28bd7587) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000fa) state: ok
OK LUN:000 AVAGO Serial Attached SCSI Disk (naa.600605b00ba8d090203f04c62b3418e7) state: ok
OK LUN:000 Local ATA Disk (t10.ATA_____INTEL_SSDSC2BX200G4_____________________BTHC714504MK200TGN__) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000ae) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000ee) state: ok
OK LUN:000 AVAGO Serial Attached SCSI Disk (naa.600605b00ba8d090203f05032ece21fb) state: ok
```

```
$ check_vsphere host-storage  -u naemon@vsphere.local  -s vcenter.example.com  \
    --vihost esx-1.example.com --allowed LEFTHAND
VSPHERE-STORAGE OK - LUNs: 12; ignored: 5; ok: 7
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae650000000000000116) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b0) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b2) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000b4) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000fa) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000ae) state: ok
OK LUN:000 LEFTHAND iSCSI Disk (naa.6000eb34b50dae6500000000000000ee) state: ok
```

```
$ check_vsphere host-storage  -u naemon@vsphere.local  -s vcenter.example.com \
    --vihost esx1.example.com --mode adapter
VSPHERE-STORAGE CRITICAL - Adapters 4; online: 1; unknown: 3
Wellsburg AHCI Controller vmhba0 (unknown)
Wellsburg AHCI Controller vmhba1 (unknown)
MegaRAID SAS Invader Controller vmhba2 (unknown)
iSCSI Software Adapter vmhba64 (online)
```

```
$ check_vsphere host-storage  -u naemon@vsphere.local  -s vcenter.example.com \
    --vihost esx1.example.com --mode adapter --allowed vmhba64
VSPHERE-STORAGE OK - Adapters 4; ignored: 3; online: 1
iSCSI Software Adapter vmhba64 (online)
```
