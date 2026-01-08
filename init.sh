#!/bin/sh
set -eu

# Prepare cgroups v2 subtree for BenchExec inside this container.
# This follows benchexec/doc/benchexec-in-container.md (non-systemd, cgroups v2).

# Some distros mount cgroup2 read-only by default; require --privileged for this to work.

# init：用于把当前 PID（容器内的 PID 1）迁移进去，从而“释放”根 cgroup 以便做委派（delegation）
# benchexec：作为 runexec 的工作子树，使用--no-container模式，后续 runexec 会严格在此之下创建自己的 cgroup
mkdir -p /sys/fs/cgroup/init /sys/fs/cgroup/benchexec || true


# Move this init process into its own cgroup to free up the root for delegation
if [ -w /sys/fs/cgroup/init/cgroup.procs ]; then
  echo $$ > /sys/fs/cgroup/init/cgroup.procs || true # $$ 是当前 shell 的 PID（在容器中通常是 PID 1），把当前进程移出根 cgroup，释放根 cgroup 用于“只承载子 cgroup（而非进程）”的委派模式
fi


# Enable all controllers on the root and on the benchexec subtree
if [ -r /sys/fs/cgroup/cgroup.controllers ]; then
  for controller in $(cat /sys/fs/cgroup/cgroup.controllers); do #cgroups v2 根目录下的 cgroup.controllers 列出当前内核可用的控制器（例如 cpu memory cpuset pids io ...）。只有在父节点的 cgroup.subtree_control 里显式 + 开启，子 cgroup 才能使用对应控制器。
    # 开启根 cgroup 和 benchexec 子树的所有控制器
    if [ -w /sys/fs/cgroup/cgroup.subtree_control ]; then
      echo +$controller > /sys/fs/cgroup/cgroup.subtree_control || true
    fi
    if [ -w /sys/fs/cgroup/benchexec/cgroup.subtree_control ]; then
      echo +$controller > /sys/fs/cgroup/benchexec/cgroup.subtree_control || true
    fi
  done
fi

exec "$@"

