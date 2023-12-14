p=${PYTHON:-$HOME/.virtualenvs/pyvmomi/bin/python}
OPTS=(-nossl -s 127.0.0.1 -o 8989 -u user -p pass)

check() {
    local code=$1; shift;
    local cmd=$1; shift;
    local out
    local cmd=("$p" -m checkvsphere.cli $cmd "${OPTS[@]}" "$@")
    out=$("${cmd[@]}")
    local r=$?
    if [ $r -ne $code ] ; then
        echo "failed: ${cmd[*]}"
        echo "got $r"
        echo "expected $code"
        printf '%s\n' "$out"
        exit
    fi
}

check 0 about
check 2 datastores --allowed ftpint --warning '80:'

check 0 snapshots --mode age --warning 0 --banned 'wazuh|test|roc|cm2'
check 1 snapshots --mode age --warning 1
check 0 snapshots --mode age --warning 10000
check 1 snapshots --mode count --warning 1
check 0 snapshots --mode count --warning 10000
check 2 snapshots --mode age --critical 1
check 0 snapshots --mode age --critical 10000
check 2 snapshots --mode count --critical 1
check 0 snapshots --mode count --critical 10000
check 1 snapshots --mode count --warning 1
check 0 snapshots --mode count --warning 5

check 2 media
check 0 media --banned 'dc1|mbd|roc|azubi|target2'
check 0 power-state
check 0 hostnic  --vihost esx-int-13.m.consol.de
check 0 hostruntime  --vihost esx-int-13.m.consol.de --mode=health

# hoststorage and hostservice don't work with the simulator :(

check 0 perf  --vimtype HostSystem --vimname esx-int-12.m.consol.de  --perfcounter cpu:usage:average --maintenance-state=OK
check 1 perf  --vimtype HostSystem --vimname esx-int-12.m.consol.de  --perfcounter cpu:usage:average --maintenance-state=WARNING
check 2 perf  --vimtype HostSystem --vimname esx-int-12.m.consol.de  --perfcounter cpu:usage:average --maintenance-state=CRITICAL
check 3 perf  --vimtype HostSystem --vimname esx-int-12.m.consol.de  --perfcounter cpu:usage:average --maintenance-state=UNKNOWN
check 3 perf  --vimtype HostSystem --vimname esx-int-12.m.consol.de  --perfcounter cpu:usage:average
check 0 perf  --vimtype HostSystem --vimname esx-int-13.m.consol.de  --perfcounter cpu:usage:average

check 0 hoststorage  --vihost esx-int-12.m.consol.de --maintenance-state=OK --mode=lun
check 1 hoststorage  --vihost esx-int-12.m.consol.de --maintenance-state=WARNING --mode=lun
check 2 hoststorage  --vihost esx-int-12.m.consol.de --maintenance-state=CRITICAL --mode=lun
check 3 hoststorage  --vihost esx-int-12.m.consol.de --maintenance-state=UNKNOWN --mode=lun
check 3 hoststorage  --vihost esx-int-12.m.consol.de --mode=lun

check 0 hostservice  --vihost esx-int-12.m.consol.de --maintenance-state=OK
check 1 hostservice  --vihost esx-int-12.m.consol.de --maintenance-state=WARNING
check 2 hostservice  --vihost esx-int-12.m.consol.de --maintenance-state=CRITICAL
check 3 hostservice  --vihost esx-int-12.m.consol.de --maintenance-state=UNKNOWN
check 3 hostservice  --vihost esx-int-12.m.consol.de

check 0 hostruntime  --vihost esx-int-12.m.consol.de --maintenance-state=OK --mode=health
check 1 hostruntime  --vihost esx-int-12.m.consol.de --maintenance-state=WARNING --mode=health
check 2 hostruntime  --vihost esx-int-12.m.consol.de --maintenance-state=CRITICAL --mode=health
check 3 hostruntime  --vihost esx-int-12.m.consol.de --maintenance-state=UNKNOWN --mode=health
check 3 hostruntime  --vihost esx-int-12.m.consol.de --mode=health

check 0 hostnic  --vihost esx-int-12.m.consol.de --maintenance-state=OK
check 1 hostnic  --vihost esx-int-12.m.consol.de --maintenance-state=WARNING
check 2 hostnic  --vihost esx-int-12.m.consol.de --maintenance-state=CRITICAL
check 3 hostnic  --vihost esx-int-12.m.consol.de --maintenance-state=UNKNOWN
check 3 hostnic  --vihost esx-int-12.m.consol.de
