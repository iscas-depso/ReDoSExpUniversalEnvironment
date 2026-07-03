#!/usr/bin/env bash
set -euo pipefail

DATASET_FILE="${1:?usage: panda_linguafranca_full.sh <dataset-file> <tag> [import-db]}"
TS="${2:?usage: panda_linguafranca_full.sh <dataset-file> <tag> [import-db]}"
IMPORT_DB_FILE="${3:-}"

RESULTS_DIR="/pub/data/lirc/results"
WORK_DIR="/pub/data/lirc/ReDoSExpUniversalEnvironment"
DATASET_DIR="$(dirname "${DATASET_FILE}")"
DATASET_BASENAME="$(basename "${DATASET_FILE}")"
DATASET_STEM="${DATASET_BASENAME%.*}"
HOST_TAG="$(hostname -s)"
TOTAL_CORES="$(nproc)"
IMPORT_DB_ARG=""

if [[ -n "${IMPORT_DB_FILE}" ]]; then
  IMPORT_DB_ARG="--import-db /results/$(basename "${IMPORT_DB_FILE}")"
fi

if (( TOTAL_CORES > 5 )); then
  WORKERS=$((TOTAL_CORES - 5))
  CPUSET="5-$((TOTAL_CORES - 1))"
else
  WORKERS=1
  CPUSET="0-$((TOTAL_CORES - 1))"
fi

DB_FILE="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}.db"
LOG_FILE="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}.log"
STATUS_FILE="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}.status"
CID_FILE="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}.cid"
PID_FILE="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}.pid"
INNER_SCRIPT="${RESULTS_DIR}/${DATASET_STEM}_full_${HOST_TAG}_${TS}_inner.sh"
NAME="${DATASET_STEM}-full-${HOST_TAG}-${TS}"

mkdir -p "${RESULTS_DIR}"

cat > "${INNER_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
set -e
controllers="$(cat /sys/fs/cgroup/cgroup.controllers)"
mkdir -p /sys/fs/cgroup/init /sys/fs/cgroup/benchexec
echo $$ > /sys/fs/cgroup/init/cgroup.procs
for controller in $controllers; do
  echo +$controller > /sys/fs/cgroup/cgroup.subtree_control || true
  echo +$controller > /sys/fs/cgroup/benchexec/cgroup.subtree_control || true
done
cd /app
python3 Gen.py "/dataset/__DATASET_BASENAME__" "/results/__DB_BASENAME__" __IMPORT_DB_ARG__ --workers __WORKERS__ --cpu-cores 1 --timeout-seconds 600
python3 Verify.py "/results/__DB_BASENAME__" 100 0 --candidate-policy all --workers __WORKERS__ --cpu-cores 1 --timeout-seconds 10
EOF

sed -i \
  -e "s#__DATASET_BASENAME__#${DATASET_BASENAME}#g" \
  -e "s#__DB_BASENAME__#$(basename "${DB_FILE}")#g" \
  -e "s#__IMPORT_DB_ARG__#${IMPORT_DB_ARG}#g" \
  -e "s#__WORKERS__#${WORKERS}#g" \
  "${INNER_SCRIPT}"

chmod +x "${INNER_SCRIPT}"

nohup bash -lc "
cid=\$(docker run -d --name '${NAME}' --user root --privileged --cgroupns=host \
  --cpuset-cpus='${CPUSET}' \
  -v '${WORK_DIR}:/app' \
  -v '${DATASET_DIR}:/dataset' \
  -v '${RESULTS_DIR}:/results' \
  -v /tmp:/tmp \
  redos-test:latest \
  bash '/results/$(basename "${INNER_SCRIPT}")')
printf '%s\n' \"\${cid}\" > '${CID_FILE}'
docker logs -f \"\${cid}\" > '${LOG_FILE}' 2>&1 &
log_pid=\$!
while true; do
  running=\$(docker inspect -f '{{.State.Running}}' \"\${cid}\" 2>/dev/null || echo missing)
  if [ \"\${running}\" != 'true' ]; then
    break
  fi
  sleep 30
done
rc=\$(docker inspect -f '{{.State.ExitCode}}' \"\${cid}\" 2>/dev/null || echo 125)
wait \"\${log_pid}\" || true
printf '%s\n' \"\${rc}\" > '${STATUS_FILE}'
docker rm -f \"\${cid}\" >/dev/null 2>&1 || true
exit 0
" > /dev/null 2>&1 < /dev/null &

HOST_PID=$!

printf '%s\n' "${HOST_PID}" > "${PID_FILE}"
printf '%s\n' "${DB_FILE}"
printf '%s\n' "${LOG_FILE}"
printf '%s\n' "${STATUS_FILE}"
printf '%s\n' "${CID_FILE}"
printf '%s\n' "${PID_FILE}"
printf '%s\n' "${INNER_SCRIPT}"
