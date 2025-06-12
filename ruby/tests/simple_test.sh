#!/bin/bash

# Simple test script for Ruby benchmark program

echo "=== Running Simple Ruby Benchmark Test ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ruby is available
if ! command -v ruby &> /dev/null; then
    echo -e "${RED}FAILED: ruby not found${NC}"
    echo "Please install Ruby."
    exit 1
fi

# Check if the program exists
if [ ! -f "../benchmark.rb" ]; then
    echo -e "${RED}FAILED: benchmark.rb not found${NC}"
    exit 1
fi

echo -e "${GREEN}Found benchmark.rb${NC}"
echo

# Simple test: Count "cat" occurrences in simple_test.txt
echo -e "${YELLOW}Running simple test...${NC}"
echo "  Test: Count 'cat' occurrences in simple_test.txt"

# Base64 encode "cat" -> Y2F0
result=$(ruby ../benchmark.rb "Y2F0" "simple_test.txt" "0" 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo -e "  ${RED}FAILED: Program exited with code $exit_code${NC}"
    echo "  Output: $result"
    exit 1
fi

# Extract match count from result (format: "time - count")
match_count=$(echo "$result" | cut -d'-' -f2 | tr -d ' ')
elapsed_time=$(echo "$result" | cut -d'-' -f1 | tr -d ' ')

echo "  Result: $elapsed_time ms, $match_count matches"

# Check if we got a reasonable result (should find "cat" at least once)
if [ "$match_count" -gt 0 ]; then
    echo -e "  ${GREEN}PASSED: Found $match_count matches${NC}"
    echo
    echo -e "${GREEN}Simple test completed successfully!${NC}"
    exit 0
else
    echo -e "  ${RED}FAILED: Expected at least 1 match, got $match_count${NC}"
    exit 1
fi 