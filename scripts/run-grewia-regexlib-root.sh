#!/usr/bin/env bash
set -euo pipefail

TS="${1:-$(date +%Y%m%d_%H%M%S)}"
DB_NAME="regexlib_grewia_600s_local_refresh2_${TS}.db"
LOG_NAME="regexlib_grewia_600s_local_refresh2_${TS}.log"
DB="/pub/data/lirc/results/${DB_NAME}"
LOG="/pub/data/lirc/results/${LOG_NAME}"
PIDFILE="/pub/data/lirc/results/regexlib_grewia_600s_local_refresh2_${TS}.pid"
NAME="grewia-batch-${TS}"

CID="$(docker run -d --rm --name "$NAME" --user root --privileged --cgroupns=host \
  -v /pub/data/lirc/ReDoSExpUniversalEnvironment:/workspace \
  -v /pub/data/lirc/dataset:/dataset \
  -v /pub/data/lirc/results:/results \
  -v /tmp:/tmp \
  -e BATCH_DB="/results/${DB_NAME}" \
  -e BATCH_LOG="/results/${LOG_NAME}" \
  redos-test-current:latest \
  bash -lc '
set -e
controllers="$(cat /sys/fs/cgroup/cgroup.controllers)"
mkdir -p /sys/fs/cgroup/init /sys/fs/cgroup/benchexec
echo $$ > /sys/fs/cgroup/init/cgroup.procs
for controller in $controllers; do
  echo +$controller > /sys/fs/cgroup/cgroup.subtree_control || true
  echo +$controller > /sys/fs/cgroup/benchexec/cgroup.subtree_control || true
done
cd /workspace
python3 Gen.py /dataset/regexlib.txt "$BATCH_DB" --tools grewia --workers 251 --cpu-cores 1 --timeout-seconds 600 >"$BATCH_LOG" 2>&1
')"

printf '%s\n%s\n%s\n%s\n%s\n' "$CID" "$DB" "$LOG" "$PIDFILE" "$NAME"
echo "$CID" > "$PIDFILE"
