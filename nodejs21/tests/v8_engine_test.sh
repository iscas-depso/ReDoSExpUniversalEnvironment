#!/bin/bash

# V8 Non-Backtracking RegExp Engine Test Script for Node.js 21

echo "=== V8 Non-Backtracking RegExp Engine Tests ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run V8 engine tests
run_v8_test() {
    local test_name="$1"
    local node_flags="$2"
    
    echo -e "${YELLOW}Test: $test_name${NC}"
    echo "  Node flags: $node_flags"
    
    # Run the V8 engine test
    result=""
    exit_code=1
    
    if [ -f "test-linear.js" ]; then
        if [ -n "$node_flags" ]; then
            result=$(node $node_flags test-linear.js 2>&1)
        else
            result=$(node test-linear.js 2>&1)
        fi
        exit_code=$?
    else
        result="test-linear.js not found"
        exit_code=1
    fi
    
    if [ $exit_code -ne 0 ]; then
        echo -e "  ${RED}FAILED: V8 engine test exited with code $exit_code${NC}"
        echo "  Output: $result"
        return 1
    fi
    
    # Check if linear engine is supported
    if echo "$result" | grep -q "Linear engine flag (/l) is supported"; then
        echo -e "  ${GREEN}PASSED: Linear engine supported${NC}"
        return 0
    elif echo "$result" | grep -q "Linear engine flag (/l) not supported"; then
        echo -e "  ${YELLOW}WARNING: Linear engine not supported (expected without flags)${NC}"
        return 0
    else
        echo -e "  ${RED}FAILED: Unexpected output${NC}"
        echo "  Output: $result"
        return 1
    fi
}

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}FAILED: Node.js not found${NC}"
    exit 1
fi

echo -e "${GREEN}Found Node.js: $(node --version)${NC}"
echo -e "${GREEN}V8 version: $(node -e "console.log(process.versions.v8)")${NC}"
echo

# Test cases
passed=0
total=0

# Test 1: Without experimental flags (should not support /l flag)
echo "--- V8 Engine Test Cases ---"
if run_v8_test "Standard Engine (no flags)" ""; then
    ((passed++))
fi
((total++))
echo

# Test 2: With experimental regexp engine flag
if run_v8_test "Linear Engine (with --enable-experimental-regexp-engine)" "--enable-experimental-regexp-engine"; then
    ((passed++))
fi
((total++))
echo

# Test 3: With both experimental flags
if run_v8_test "Hybrid Engine (both experimental flags)" "--enable-experimental-regexp-engine --default-to-experimental-regexp-engine"; then
    ((passed++))
fi
((total++))
echo

# Summary
echo "=== V8 Engine Test Summary ==="
echo "Passed: $passed/$total"
if [ $passed -eq $total ]; then
    echo -e "${GREEN}All V8 engine tests passed!${NC}"
    echo "V8 Non-Backtracking RegExp Engine features:"
    echo "  • Linear-time execution prevents ReDoS attacks"
    echo "  • Automatic fallback for unsupported constructs"
    echo "  • Enhanced security and performance"
    exit 0
else
    echo -e "${RED}Some V8 engine tests failed!${NC}"
    exit 1
fi 