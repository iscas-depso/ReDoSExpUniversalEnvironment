#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-redos-test}"
DATASET="${DATASET:-/app/expr/data/cve414_with_metadata_no_slq_only.jsonl}"
OUTPUT="${OUTPUT:-./expr/tmp/ere_detect_bv_cve414_with_metadata_no_slq_only.json}"
PYTHON_SCRIPT="${PYTHON_SCRIPT:-/app/expr/filter_ere_accepted.py}"
TIMEOUT="${TIMEOUT:-30}"

EXTRA_DOCKER_ARGS=()
PYTHON_ARGS=()

for arg in "$@"; do
    if [[ "${arg}" == "--cgroupv1" ]]; then
        EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
        continue
    fi
    PYTHON_ARGS+=("${arg}")
done

mkdir -p "$(dirname "${OUTPUT}")"

docker run --rm --privileged \
    "${EXTRA_DOCKER_ARGS[@]}" \
    --tmpfs /tmp:rw \
    -v ./expr:/app/expr \
    "${IMAGE}" \
    python3 "${PYTHON_SCRIPT}" \
        --input "${DATASET}" \
        --timeout "${TIMEOUT}" \
        "${PYTHON_ARGS[@]}" \
    > "${OUTPUT}"

echo "Saved filtered ERE-accepted patterns to ${OUTPUT}"
