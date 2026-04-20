#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${REDOS_TEST_IMAGE:-redos-test-grewia-real}"
BASE_IMAGE="${BASE_IMAGE:-}"
PROXY="${PROXY:-}"
FORCE_REBUILD="${FORCE_REBUILD:-0}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for test:grewia:real but was not found in PATH." >&2
  exit 1
fi

base_candidates=()
if [[ -n "${BASE_IMAGE}" ]]; then
  base_candidates+=("${BASE_IMAGE}")
else
  base_candidates+=(
    "ubuntu:22.04"
    "docker.1ms.run/library/ubuntu:22.04"
    "docker.m.daocloud.io/library/ubuntu:22.04"
    "docker.kejilion.pro/library/ubuntu:22.04"
    "docker.xuanyuan.me/library/ubuntu:22.04"
    "docker.hlmirror.com/library/ubuntu:22.04"
    "run-docker.cn/library/ubuntu:22.04"
  )
fi

if [[ "${FORCE_REBUILD}" == "1" ]] || ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  build_succeeded=0
  for candidate in "${base_candidates[@]}"; do
    build_args=(--build-arg "BASE_IMAGE=${candidate}")
    if [[ -n "${PROXY}" ]]; then
      build_args+=(--build-arg "PROXY=${PROXY}")
    fi

    echo "Building ${IMAGE} with BASE_IMAGE=${candidate}"
    if docker build "${build_args[@]}" -t "${IMAGE}" "${ROOT_DIR}"; then
      build_succeeded=1
      break
    fi
  done

  if [[ "${build_succeeded}" != "1" ]]; then
    echo "Failed to build ${IMAGE} with all configured base image sources." >&2
    exit 1
  fi
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

regex_b64="$(node -e "process.stdout.write(Buffer.from('a+','utf8').toString('base64'))")"

docker run --rm \
  -v "${tmpdir}:/out" \
  "${IMAGE}" \
  bash -lc "python3 /app/tools/grewia/run.py '${regex_b64}' /out/default.json"

docker run --rm \
  -e GREWIA_REGEX_ENGINE=Python \
  -e GREWIA_MATCH_MODE=1 \
  -e GREWIA_ATTACK_STRING_LENGTH=4096 \
  -e GREWIA_CANDIDATE_MODE=multiple \
  -e GREWIA_DECREMENTAL=1 \
  -v "${tmpdir}:/out" \
  "${IMAGE}" \
  bash -lc "python3 /app/tools/grewia/run.py '${regex_b64}' /out/custom.json"

node - "${tmpdir}/default.json" "${tmpdir}/custom.json" <<'NODE'
const fs = require('node:fs');
const assert = require('node:assert');

const [defaultPath, customPath] = process.argv.slice(2);
const defaultRun = JSON.parse(fs.readFileSync(defaultPath, 'utf8'));
const customRun = JSON.parse(fs.readFileSync(customPath, 'utf8'));

function assertCommonShape(label, payload) {
  assert.strictEqual(typeof payload.elapsed_ms, 'number', `${label}: elapsed_ms must be numeric`);
  assert.strictEqual(typeof payload.is_redos, 'boolean', `${label}: is_redos must be boolean`);
  assert.ok(Object.prototype.hasOwnProperty.call(payload, 'prefix'), `${label}: prefix missing`);
  assert.ok(Object.prototype.hasOwnProperty.call(payload, 'infix'), `${label}: infix missing`);
  assert.ok(Object.prototype.hasOwnProperty.call(payload, 'suffix'), `${label}: suffix missing`);
  assert.ok(Object.prototype.hasOwnProperty.call(payload, 'repeat_times'), `${label}: repeat_times missing`);
  assert.ok(Array.isArray(payload.candidates), `${label}: candidates must be an array`);
  assert.ok(payload.toolMeta && payload.toolMeta.normalizedOptions, `${label}: toolMeta.normalizedOptions missing`);
}

assertCommonShape('default', defaultRun);
assert.deepStrictEqual(defaultRun.toolMeta.normalizedOptions, {
  regexEngine: 'Java',
  matchMode: 0,
  attackStringLength: 100000,
  candidateMode: 'single',
  decremental: false
});

assertCommonShape('custom', customRun);
assert.deepStrictEqual(customRun.toolMeta.normalizedOptions, {
  regexEngine: 'Python',
  matchMode: 1,
  attackStringLength: 4096,
  candidateMode: 'multiple',
  decremental: true
});
NODE

echo "GREWIA real smoke test passed."
