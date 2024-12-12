# next

* add vm-tools subcommand that checks for VMs that don't have vm-tools installed
  @BenjaminBoehm #25

# v0.3.12

* add `--mode path` to host-storage

# v0.3.11

* [BREAKING] add check for System.View permission to about cmd. use
  `--skip-permission` to skip this (old behavior).

# v0.3.10

* fix error in media with offline vms

# v0.3.9

* make use of sessionId support in pyVmomi for `--sessionfile`

# v0.3.8

* depend on 8.0.3.0.1 because of the vsan command, the extra non free bindings
  are now included in pyVmomi and don't exist anymore as a separate project

# v0.3.7

* limit number in plugin output to 8 significant digits

# v0.3.6

* add experimental sessionfile support (MLUECKERT)

# v0.3.5

* datastores: add support for vimtype Datacenter (MLUECKERT)

# v0.3.4

* add vm-net-dev check

# v0.3.3

* adjust object status mapping in vsan cmd

# v0.3.2

* fix status message in hostruntime

# v0.3.1

* Try harder to extract a nice message from the exceptions if CONNECT_NOFAIL is set

# v0.3.0

* BREAKING CHANGE: avoid check_multi compatible performance data. pnp4nagios has it's issues with that
* improve powerstate

# v0.2.3

* host-runtime - improved performance
