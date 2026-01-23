#!/usr/bin/env bash

set -euo pipefail

# 工具名列表（按顺序执行）
TOOLS=(
  # ere
  recheck
  redoshunter
  rengar
  rescue
  regexploit
  regexstatic
  regulator
  # 在这里继续添加
)

IMAGE="redos-test"
# DATASET="/app/expr/data/test.jsonl"
DATASET="/app/expr/data/lookahead_fse19_fullmatch.jsonl"
# DATASET="/app/expr/data/tmp.jsonl"

for toolsname in "${TOOLS[@]}"; do
  echo "========================================"
  echo "Running tool: ${toolsname}"
  echo "========================================"

  docker run --rm --privileged \
    -v /tmp:/tmp \
    -v ./expr:/app/expr \
    "${IMAGE}" \
    /init.sh python3 /app/expr/expr.py \
      --runexec \
      --timeout 60 \
      --cpus 20 \
      --memlimit 1024 \
      --cmd "python3 /app/tools/${toolsname}/run.py" \
      "${DATASET}" \
    > "1_expr_${toolsname}.json"

  echo "Finished: ${toolsname}"
done

echo "All tools finished."
