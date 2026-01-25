#!/usr/bin/env bash

set -euo pipefail

# 工具名列表（按顺序执行）
TOOLS=(
    ere
    recheck
#   redoshunter
#   rengar
#   rescue
#   regexploit
#   regexstatic
#   regulator
)

# 引擎名列表
ENGINES=(
    # c
    # perl
    # csharp
    java11
    # python
    # nodejs14
    # java8
)


EXTRA_DOCKER_ARGS=()
if [[ "$*" == *"--cgroupv1"* ]]; then
    EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
fi

IMAGE="redos-test"
DATASETDIR="/app/expr"
PARTS=20


for engine in "${ENGINES[@]}"; do
    for toolsname in "${TOOLS[@]}"; do
        echo "========================================"
        echo "Running ${engine}_${toolsname}"
        echo "========================================"
        output_file="./expr/results/${engine}/1_detect_${toolsname}.json"
        : > $output_file
        
        for ((part=0; part<PARTS; part++)); do
            docker run --rm --privileged \
                "${EXTRA_DOCKER_ARGS[@]}" \
                --tmpfs /tmp:rw \
                -v ./expr:/app/expr \
                "${IMAGE}" \
                python3 /app/expr/detector.py \
                --runexec \
                --timeout 5 \
                --cpus 30 \
                --memlimit 10240 \
                --attack-size 100 \
                --fullmatch \
                --total-parts $PARTS \
                --part-index $part \
                --enable-cpu-monitor \
                --cmd "/app/engines/${engine}/bin/benchmark" \
                "${DATASETDIR}/results/1_expr_${toolsname}.json" \
                >>$output_file
        done

        echo "Finished: ${engine}_${toolsname}"
    done
done

echo "All tools finished."
