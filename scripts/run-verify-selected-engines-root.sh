#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <db_path> [match_mode] [timeout_seconds] [engines_csv|all]" >&2
  exit 1
fi

DB_HOST="$1"
MATCH_MODE="${2:-0}"
TIMEOUT_SECONDS="${3:-120}"
ENGINES="${4:-csharp_nonbacktracking,go,grep,nodejs21,re2,java8,nodejs14}"
DB_NAME="$(basename "$DB_HOST")"
BASE_NAME="${DB_NAME%.db}"
ENGINE_TAG="$(printf '%s' "$ENGINES" | tr ',' '_' | tr -cd 'A-Za-z0-9_-')"
if [ "$ENGINES" = "all" ]; then
  ENGINE_TAG="all"
fi
LOG="/pub/data/lirc/results/${BASE_NAME}.verify_${ENGINE_TAG}_${TIMEOUT_SECONDS}s.log"
PIDFILE="/pub/data/lirc/results/${BASE_NAME}.verify_${ENGINE_TAG}_${TIMEOUT_SECONDS}s.pid"
NAME="verify-selected-$(date +%Y%m%d_%H%M%S)"

CID="$(docker run -d --rm --name "$NAME" --user root --privileged --cgroupns=host \
  -v /pub/data/lirc/ReDoSExpUniversalEnvironment:/workspace \
  -v /pub/data/lirc/results:/results \
  -v /tmp:/tmp \
  -e BATCH_DB="/results/${DB_NAME}" \
  -e BATCH_LOG="/results/$(basename "$LOG")" \
  -e VERIFY_MATCH_MODE="$MATCH_MODE" \
  -e VERIFY_TIMEOUT_SECONDS="$TIMEOUT_SECONDS" \
  -e VERIFY_ENGINES="$ENGINES" \
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
  if [ "$VERIFY_ENGINES" = "all" ]; then
    python3 Verify.py "$BATCH_DB" 128 "$VERIFY_MATCH_MODE" --timeout-seconds "$VERIFY_TIMEOUT_SECONDS" >"$BATCH_LOG" 2>&1
  else
    python3 Verify.py "$BATCH_DB" 128 "$VERIFY_MATCH_MODE" --engines "$VERIFY_ENGINES" --timeout-seconds "$VERIFY_TIMEOUT_SECONDS" >"$BATCH_LOG" 2>&1
  fi
  ')"

printf '%s\n%s\n%s\n%s\n%s\n' "$CID" "$DB_HOST" "$LOG" "$PIDFILE" "$NAME"
echo "$CID" > "$PIDFILE"
