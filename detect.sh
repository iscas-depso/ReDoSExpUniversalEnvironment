#!/usr/bin/env bash

set -euo pipefail

# 工具名列表（按顺序执行）
TOOLS=(
  ere
  recheck
  redoshunter
  rengar
  rescue
  regexploit
  regexstatic
  regulator
)

# 引擎名列表
ENGINES=(
  nodejs14
)


IMAGE="redos-test"
DATASETDIR="/app/expr/"
for engine in "${ENGINES[@]}"; do
    for toolsname in "${TOOLS[@]}"; do
    echo "========================================"
    echo "Running ${engine}_${toolsname}"
    echo "========================================"

    docker run --rm --privileged \
        -v /tmp:/tmp \
        -v ./expr:/app/expr \
        "${IMAGE}" \
        /init.sh python3 /app/expr/expr.py \
        --runexec \
        --timeout 5 \
        --cpus 64 \
        --memlimit 10240 \
        --fullmatch \
        --cmd "/app/engine/${engine}/bin/benchmark" \
        "${DATASETDIR}/1_expr_${toolsname}.json" \
        > "1_detect_${engine}_${toolsname}.json"

    echo "Finished: ${engine}_${toolsname}"
    done
done

echo "All tools finished."
