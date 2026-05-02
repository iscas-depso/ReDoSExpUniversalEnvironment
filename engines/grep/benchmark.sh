#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$SCRIPT_DIR/benchmark.py" ]; then
  PYTHON_SCRIPT="$SCRIPT_DIR/benchmark.py"
else
  PYTHON_SCRIPT="$(dirname -- "$SCRIPT_DIR")/benchmark.py"
fi

exec python3 "$PYTHON_SCRIPT" "$@"
