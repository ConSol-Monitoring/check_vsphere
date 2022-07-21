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
| `--vimtype VIMTYPE` | the object type to check,<br/>it's a [managed object](https://vdc-repo.vmware.com/vmwb-repository/dcr-public/1ef6c336-7bef-477d-b9bb-caa1767d7e30/82521f49-9d9a-42b7-b19b-9e6cd9b30db1/vim.ManagedEntity.html) like: HostSystem, Datacenter or VirtualMachine |
| `--vimname VIMNAME` | the name of the ManagedObject of vimtype  |
| `--warning WARNING`     | warning [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |
| `--critical CRITICAL`   | critical [threshold](https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT) |

