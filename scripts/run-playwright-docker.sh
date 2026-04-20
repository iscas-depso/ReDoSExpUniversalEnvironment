#!/usr/bin/env bash
# Run Playwright E2E tests inside the official Playwright container.
# This is intended for hosts that cannot satisfy browser runtime deps locally.
set -euo pipefail

IMAGE="${PLAYWRIGHT_DOCKER_IMAGE:-mcr.microsoft.com/playwright:v1.56.0-jammy}"
WORKDIR="/work"
HOST_OUTPUT_DIR="${PLAYWRIGHT_OUTPUT_DIR:-/tmp/redos-playwright-results}"
CONTAINER_OUTPUT_ROOT="/playwright-output"
CONTAINER_OUTPUT_DIR="${CONTAINER_OUTPUT_ROOT}/results"
PORT="${PLAYWRIGHT_PORT:-3100}"

mkdir -p "${HOST_OUTPUT_DIR}"

exec docker run --rm \
  --ipc=host \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp/playwright-home \
  -e PLAYWRIGHT_PORT="${PORT}" \
  -e PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
  -v "$(pwd):${WORKDIR}" \
  -v "${HOST_OUTPUT_DIR}:${CONTAINER_OUTPUT_ROOT}" \
  -w "${WORKDIR}" \
  "${IMAGE}" \
  bash -lc "mkdir -p \"\$HOME\" '${CONTAINER_OUTPUT_ROOT}' && npx playwright test --output='${CONTAINER_OUTPUT_DIR}' \"$@\""
