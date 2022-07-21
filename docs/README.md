# check\_vsphere

This is a monitoring plugin for naemon, nagios or icinga compatible systems that
can check various things against the vSphere API. It meant as a replacement for
`check_vmware_esx`, `check_vmware_api` and the like that are all written in
Perl. This rewrite is needed because the Perl SDK for the vSphere API was [marked
deprecated](https://developer.vmware.com/sdks) by VMware.

The only supported programming alternatives are Java and Python. We chose python
for the implementation.
