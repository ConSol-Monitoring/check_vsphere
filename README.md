# About

This is a monitoring plugin for naemon, icinga, nagios like systems. It
is meant as a successor of check\_vmware\_esx. check\_vmware\_esx is written
Perl but VMWare™ has dropped support for the Perl SDK. So this plugin is written
in Python using pyVmomi.

## Features

The plugin has modes to check various aspects of these components:

* datastores
* host-runtime
* host-service
* host-storage
* host-nic
* snapshots
* vsan

Check the
[Documentation](https://omd.consol.de/docs/plugins/check_vsphere/)
for further details.

# Installation

```
pip install checkvsphere
```

# LICENSE

If not stated otherwise in a source file everything is licensed under
GNU AFFERO GENERAL PUBLIC LICENSE Version 3.

See also the LICENSE file.
