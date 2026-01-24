#!/usr/bin/env bash

set -euo pipefail

# 工具名列表（按顺序执行）
TOOLS=(
  recheck
  ere
  redoshunter
  rengar
  rescue
  regexploit
  regexstatic
#   regulator
)

# 引擎名列表
ENGINES=(
    c
    perl
    csharp
    java11
    python
    nodejs14
    java8
)


EXTRA_DOCKER_ARGS=()
if [[ "$*" == *"--cgroupv1"* ]]; then
    EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
fi

IMAGE="redos-test"
DATASETDIR="/app/expr"
for engine in "${ENGINES[@]}"; do
    for toolsname in "${TOOLS[@]}"; do
    echo "========================================"
    echo "Running ${engine}_${toolsname}"
    echo "========================================"

    docker run --rm --privileged \
        "${EXTRA_DOCKER_ARGS[@]}" \
        --tmpfs /tmp:rw \
        -v ./expr:/app/expr \
        "${IMAGE}" \
        python3 /app/expr/detector.py \
        --runexec \
        --timeout 5 \
        --cpus 64 \
        --memlimit 10240 \
        --attack-size 100 \
        --fullmatch \
        --cmd "/app/engines/${engine}/bin/benchmark" \
        "${DATASETDIR}/1_expr_${toolsname}.json" \
        > "./expr/1_detect_${engine}_${toolsname}.json"

    echo "Finished: ${engine}_${toolsname}"
    done
done

echo "All tools finished."
