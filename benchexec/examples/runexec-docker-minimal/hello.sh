#!/bin/sh
set -eu

echo "hello from tool"
uname -a || true
# Write a small output file to verify result file handling
echo "artifact from tool" > output.txt

