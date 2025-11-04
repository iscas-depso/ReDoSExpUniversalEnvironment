#!/bin/sh
set -eu

# Prepare cgroups v2 subtree for BenchExec inside this container.
# This follows benchexec/doc/benchexec-in-container.md (non-systemd, cgroups v2).

# Some distros mount cgroup2 read-only by default; require --privileged for this to work.

mkdir -p /sys/fs/cgroup/init /sys/fs/cgroup/benchexec || true
# Move this init process into its own cgroup to free up the root for delegation
if [ -w /sys/fs/cgroup/init/cgroup.procs ]; then
  echo $$ > /sys/fs/cgroup/init/cgroup.procs || true
fi

# Enable all controllers on the root and on the benchexec subtree
if [ -r /sys/fs/cgroup/cgroup.controllers ]; then
  for controller in $(cat /sys/fs/cgroup/cgroup.controllers); do
    if [ -w /sys/fs/cgroup/cgroup.subtree_control ]; then
      echo +$controller > /sys/fs/cgroup/cgroup.subtree_control || true
    fi
    if [ -w /sys/fs/cgroup/benchexec/cgroup.subtree_control ]; then
      echo +$controller > /sys/fs/cgroup/benchexec/cgroup.subtree_control || true
    fi
  done
fi

exec "$@"

