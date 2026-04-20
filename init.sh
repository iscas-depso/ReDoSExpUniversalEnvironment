#!/bin/sh
set -eu

fail_cgroup() {
  echo "FATAL: BenchExec requires writable cgroups v2 inside the container." >&2
  echo "FATAL: $1" >&2
  echo "FATAL: Start the service with: docker run --rm --privileged --cgroupns=host -p 8080:8080 -v /tmp:/tmp redos-test" >&2
  exit 1
}

needs_benchexec_cgroups() {
  if [ "${1:-}" = "npm" ] && [ "${2:-}" = "start" ]; then
    return 0
  fi
  if [ "${1:-}" = "node" ] && [ "${2:-}" = "server/index.js" ]; then
    return 0
  fi
  return 1
}

if needs_benchexec_cgroups "$@"; then
  cgroup_mount="$(awk '$2=="/sys/fs/cgroup"{print $3" "$4; exit}' /proc/mounts)"
  [ -n "$cgroup_mount" ] || fail_cgroup "/sys/fs/cgroup is not mounted in the container."

  cgroup_fs="$(printf '%s' "$cgroup_mount" | cut -d' ' -f1)"
  cgroup_opts="$(printf '%s' "$cgroup_mount" | cut -d' ' -f2-)"
  [ "$cgroup_fs" = "cgroup2" ] || fail_cgroup "/sys/fs/cgroup is mounted as '$cgroup_fs', expected cgroup2."

  case ",$cgroup_opts," in
    *,rw,*) ;;
    *) fail_cgroup "/sys/fs/cgroup is mounted read-only with options '$cgroup_opts'." ;;
  esac

  controllers="$(cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null || true)"
  [ -n "$controllers" ] || fail_cgroup "Cannot read /sys/fs/cgroup/cgroup.controllers."

  for required in cpu memory pids; do
    printf '%s\n' "$controllers" | grep -qw "$required" || \
      fail_cgroup "Required controller '$required' is missing. Available controllers: $controllers"
  done

  mkdir -p /sys/fs/cgroup/init /sys/fs/cgroup/benchexec || \
    fail_cgroup "Failed to create /sys/fs/cgroup/init or /sys/fs/cgroup/benchexec."

  [ -w /sys/fs/cgroup/init/cgroup.procs ] || \
    fail_cgroup "/sys/fs/cgroup/init/cgroup.procs is not writable."
  echo $$ > /sys/fs/cgroup/init/cgroup.procs || \
    fail_cgroup "Failed to move PID 1 into /sys/fs/cgroup/init/cgroup.procs."

  [ -w /sys/fs/cgroup/cgroup.subtree_control ] || \
    fail_cgroup "/sys/fs/cgroup/cgroup.subtree_control is not writable."
  [ -w /sys/fs/cgroup/benchexec/cgroup.subtree_control ] || \
    fail_cgroup "/sys/fs/cgroup/benchexec/cgroup.subtree_control is not writable."

  for controller in $controllers; do
    echo "+$controller" > /sys/fs/cgroup/cgroup.subtree_control || \
      fail_cgroup "Failed to enable controller '$controller' in /sys/fs/cgroup/cgroup.subtree_control."
    echo "+$controller" > /sys/fs/cgroup/benchexec/cgroup.subtree_control || \
      fail_cgroup "Failed to enable controller '$controller' in /sys/fs/cgroup/benchexec/cgroup.subtree_control."
  done

  enabled="$(cat /sys/fs/cgroup/benchexec/cgroup.subtree_control 2>/dev/null || true)"
  for required in cpu memory pids; do
    printf '%s\n' "$enabled" | grep -qw "$required" || \
      fail_cgroup "Controller '$required' was not enabled under /sys/fs/cgroup/benchexec/cgroup.subtree_control."
  done
fi

exec "$@"
