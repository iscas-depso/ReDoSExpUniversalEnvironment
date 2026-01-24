#!/usr/bin/env bash

set -euo pipefail

# 工具名列表（按顺序执行）
TOOLS=(
  # revealer
  ere
  # recheck
  # redoshunter
  # rengar
  # rescue
  # regexploit
  # regexstatic
  # regulator
  # 在这里继续添加
)

IMAGE="redos-test"
# DATASET="/app/expr/data/test.jsonl"
DATASET="/app/expr/data/lookahead_fse19_fullmatch.jsonl"
# DATASET="/app/expr/data/tmp.jsonl"
EXTRA_DOCKER_ARGS=()
if [[ "$*" == *"--cgroupv1"* ]]; then
    EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
fi

for toolsname in "${TOOLS[@]}"; do
  echo "========================================"
  echo "Running tool: ${toolsname}"
  echo "========================================"

  docker run --rm --privileged \
    "${EXTRA_DOCKER_ARGS[@]}" \
    --tmpfs /tmp:rw \
    -v ./expr:/app/expr \
    "${IMAGE}" \
    python3 /app/expr/expr.py \
      --runexec \
      --timeout 600 \
      --cpus 20 \
      --memlimit 10240 \
      --cmd "python3 /app/tools/${toolsname}/run.py" \
      "${DATASET}" \
    > "./expr/1_expr_${toolsname}.json"

  echo "Finished: ${toolsname}"
done

echo "All tools finished."
