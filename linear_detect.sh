#!/usr/bin/env bash

set -euo pipefail

# 引擎名列表（按顺序执行）
ENGINES=(
    ere
    python
    java11
    nodejs14
)

EXTRA_DOCKER_ARGS=()
if [[ "$*" == *"--cgroupv1"* ]]; then
    EXTRA_DOCKER_ARGS=("--cgroupns=host" "-v" "/sys/fs/cgroup:/sys/fs/cgroup:rw")
fi

IMAGE="redos-test"
GROUND_TRUTH="/app/expr/ground_truth/ground_truth_all_engines.jsonl"
PARTS=20

SAMPLES=30
SEED=20260306
KS=(50 200 800 2000 4000 5000 12000 50000 150000 500000)
RUNS_PER_K=4
OUTPUT_DIR="./expr/results/2_linearity"
MANIFEST_PATH="/app/expr/results/2_linearity/samples_manifest.jsonl"

mkdir -p "$OUTPUT_DIR"

echo "========================================"
echo "Preparing shared samples manifest"
echo "========================================"

docker run --rm --privileged \
    "${EXTRA_DOCKER_ARGS[@]}" \
    --tmpfs /tmp:rw \
    -v ./:/app \
    "${IMAGE}" \
    python3 /app/expr/linear_benchmark.py \
    --runexec \
    --timeout 5 \
    --cpus 30 \
    --memlimit 10240 \
    --fullmatch \
    --samples "${SAMPLES}" \
    --seed "${SEED}" \
    --ks "${KS[@]}" \
    --runs-per-k "${RUNS_PER_K}" \
    --required-engines python java11 nodejs14 \
    --write-manifest "${MANIFEST_PATH}" \
    "${GROUND_TRUTH}" >/dev/null

echo "Manifest ready: ${OUTPUT_DIR}/samples_manifest.jsonl"

for engine in "${ENGINES[@]}"; do
    echo "========================================"
    echo "Running linear benchmark for ${engine}"
    echo "========================================"

    output_file="${OUTPUT_DIR}/${engine}.jsonl"
    : > "$output_file"

    for ((part=0; part<PARTS; part++)); do
        docker run --rm --privileged \
            "${EXTRA_DOCKER_ARGS[@]}" \
            --tmpfs /tmp:rw \
            -v ./:/app \
            "${IMAGE}" \
            python3 /app/expr/linear_benchmark.py \
            --runexec \
            --timeout 5 \
            --cpus 30 \
            --memlimit 10240 \
            --fullmatch \
            --samples "${SAMPLES}" \
            --seed "${SEED}" \
            --ks "${KS[@]}" \
            --runs-per-k "${RUNS_PER_K}" \
            --required-engines python java11 nodejs14 \
            --manifest "${MANIFEST_PATH}" \
            --total-parts "${PARTS}" \
            --part-index "${part}" \
            --enable-cpu-monitor \
            --engine "${engine}" \
            --cmd "/app/engines/${engine}/bin/benchmark" \
            >> "$output_file"
    done

    echo "Finished linear benchmark for ${engine}"
done

echo "All linear benchmark runs finished."
