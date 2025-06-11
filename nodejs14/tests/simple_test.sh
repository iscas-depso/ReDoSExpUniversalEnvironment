#!/bin/bash

# Simple test script for Node.js 14 benchmark program

echo "=== Running Node.js 14 Simple Test ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if the program exists
program_found=false
if [ -f "../bin/benchmark" ]; then
    program_path="../bin/benchmark"
    program_found=true
fi

if [ "$program_found" = false ]; then
    echo -e "${RED}FAILED: Node.js 14 benchmark program not found${NC}"
    echo "Please run 'make all' first to compile the program."
    echo "Expected location: ../bin/benchmark"
    exit 1
fi
echo -e "${GREEN}Found Node.js 14 benchmark program at: $program_path${NC}"
echo

# Simple test case
# Test: Simple word matching (partial match)
# Regex: "cat" -> base64: Y2F0
echo -e "${YELLOW}Test: Simple word match (partial)${NC}"
echo "  Regex: cat (Y2F0 in base64)"
echo "  File: simple_test.txt"
echo "  Mode: 0 (partial match)"

result=$($program_path "Y2F0" "simple_test.txt" "0" 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo -e "${RED}FAILED: Program exited with code $exit_code${NC}"
    echo "Output: $result"
    exit 1
fi

# Extract match count from result (format: "time - count")
match_count=$(echo "$result" | cut -d'-' -f2 | tr -d ' ')
elapsed_time=$(echo "$result" | cut -d'-' -f1 | tr -d ' ')

echo "  Result: $elapsed_time ms, $match_count matches"

if [ "$match_count" -gt "0" ]; then
    echo -e "${GREEN}PASSED: Found $match_count matches${NC}"
    echo
    echo "=== Test Complete ==="
    echo "Node.js 14 implementation is working correctly!"
    echo "Note: This implementation uses traditional Node.js features (CommonJS, Buffer.from, performance.now)"
    exit 0
else
    echo -e "${RED}FAILED: Expected some matches, got $match_count${NC}"
    exit 1
fi 