+++
title = "check_vsphere"
tags = [
    "vsphere"
]
[cascade]
# github_project_repo="https://github.com/ConSol/check_vsphere"
# github_repo="https://github.com/ConSol/check_vsphere"
# github_subdir="docs"
# github_branch="main"
# path_base_for_github_subdir="content/en/docs/plugins/check_vsphere/"
+++

This monitoring plugin checks various aspects of vSphere through its API for
systems compatible with Naemon, Nagios, or Icinga. It is meant as a replacement
for `check_vmware_esx`, `check_vmware_api` and the like. These are all written
in Perl. This rewrite is needed because the Perl SDK for the vSphere API was
[marked deprecated](https://developer.broadcom.com/sdks?tab=Compute%2520Virtualization) by VMware.

{{% alert title="Note" color="warning" %}}
It's **not** a drop-in replacement for any of the tools mentioned above.
{{% /alert %}}

The only supported programming alternatives are Java and Python. We chose Python
for the implementation.
