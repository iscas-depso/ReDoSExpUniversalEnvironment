#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$SCRIPT_DIR/benchmark.awk" ]; then
  AWK_SCRIPT="$SCRIPT_DIR/benchmark.awk"
else
  AWK_SCRIPT="$(dirname -- "$SCRIPT_DIR")/benchmark.awk"
fi

exec env LC_ALL=C gawk -f "$AWK_SCRIPT" "$@"
