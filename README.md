| check_vmware_esx | check_vsphere |
|---|---|
| `--select cpu --subselect usage` | `perf --perfcounter cpu:usage:average`   |
| `--select cpu --subselect ready` | `perf --perfcounter cpu:ready:summation` |
| `--select cpu --subselect wait`  | `perf --perfcounter cpu:wait:summation`  |
| `--select mem --subselect usage` | `perf --perfcounter mem:usage:average`   |
| `--select mem --subselect consumed` | `perf --perfcounter mem:consumed:average`   |
| `--select mem --subselect swapused` | `perf --perfcounter mem:swapused:average`   |
| `--select mem --subselect overhead` | `perf --perfcounter mem:overhead:average`   |
| `--select mem --subselect memctl`   | `perf --perfcounter mem:vmmemctl:average`   |


# LICENSE

If not stated otherwise in a source file everything is licensed under
GNU AFFERO GENERAL PUBLIC LICENSE Version 3.

See also the LICENSE file.
