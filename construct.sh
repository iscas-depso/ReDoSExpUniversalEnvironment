#!/usr/bin/env bash

set -euo pipefail

MODES=(
    nfa
    dfa
)

IMAGE="redos-test"
DATASET="/app/expr/data/lookahead_fse19.jsonl"
PARTS=20
TIMEOUT=30
CPUS=30
MEMLIMIT=10240
OUTPUT_DIR="./expr/results/3_construct"
ERE_BIN="/app/tools/ere/ere"

EXTRA_DOCKER_ARGS=()
if [[ "$*" == *"--cgroupv1"* ]]; then
    EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
fi

mkdir -p "$OUTPUT_DIR"

for mode in "${MODES[@]}"; do
    echo "========================================"
    echo "Running construct benchmark for ${mode}"
    echo "========================================"

    output_file="${OUTPUT_DIR}/${mode}.jsonl"
    : > "$output_file"

    for ((part=0; part<PARTS; part++)); do
        docker run --rm --privileged \
            "${EXTRA_DOCKER_ARGS[@]}" \
            --tmpfs /tmp:rw \
            -v ./:/app \
            "${IMAGE}" \
            python3 /app/expr/construct_benchmark.py \
            --runexec \
            --timeout "${TIMEOUT}" \
            --cpus "${CPUS}" \
            --memlimit "${MEMLIMIT}" \
            --enable-cpu-monitor \
            --cmd "${ERE_BIN}" \
            --mode "${mode}" \
            --total-parts "${PARTS}" \
            --part-index "${part}" \
            "${DATASET}" \
            >> "$output_file"
    done

    echo "Finished construct benchmark for ${mode}"
done

echo "All construct benchmark runs finished."
