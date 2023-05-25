# General Options

| option | description |
|---|---|
| `-s HOST, --host HOST`  | vSphere service address to connect to |
| `-o PORT, --port PORT`  | Port to connect on |
| `-u USER, --user USER`  | User name to use when connecting to host |
| `-p PASSWORD, --password` | Password to use when connecting to host, can also be set by env `VSPHERE_PASS` |
| `-nossl, --disable-ssl-verification` | Disable ssl host certificate verification |

# Common Options

| option | description |
|---|---|
| `--vihost VIHOST`   | name of the ESXi Host as seen by the vCenter |
| `--vimtype VIMTYPE` | the object type to check,<br/>it's a [managed entity](https://vdc-download.vmware.com/vmwb-repository/dcr-public/bf660c0a-f060-46e8-a94d-4b5e6ffc77ad/208bc706-e281-49b6-a0ce-b402ec19ef82/SDK/vsphere-ws/docs/ReferenceGuide/vim.ManagedEntity.html) like: HostSystem, Datacenter or VirtualMachine |
| `--vimname VIMNAME` | the name of the ManagedEntity of vimtype  |
| `--warning WARNING`     | warning [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |
| `--critical CRITICAL`   | critical [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |

# Environment Variables

| var | description |
|---|---|
| `CONNECT_NOFAIL` | if set a connection error exits with status OK |
| `TIMEOUT` | Global timeout of the plugin in seconds, defaults to `30` |
| `VSPHERE_PASS` | default value for `--password` option |
