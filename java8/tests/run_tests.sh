#!/bin/bash

# Test script for Java benchmark program

echo "=== Running Java Benchmark Tests ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a test case
run_test() {
    local test_name="$1"
    local base64_regex="$2"
    local test_file="$3"
    local match_mode="$4"
    local expected_matches="$5"
    
    echo -e "${YELLOW}Test: $test_name${NC}"
    echo "  Regex (base64): $base64_regex"
    echo "  File: $test_file"
    echo "  Mode: $match_mode ($([ "$match_mode" = "1" ] && echo "full match" || echo "partial match"))"
    
    # Run the benchmark
    result=""
    exit_code=1
    
    if [ -f "../bin/benchmark" ]; then
        result=$(../bin/benchmark "$base64_regex" "$test_file" "$match_mode" 2>&1)
        exit_code=$?
    else
        result="Executable not found"
        exit_code=1
    fi
    
    if [ $exit_code -ne 0 ]; then
        echo -e "  ${RED}FAILED: Program exited with code $exit_code${NC}"
        echo "  Output: $result"
        return 1
    fi
    
    # Extract match count from result (format: "time - count")
    match_count=$(echo "$result" | cut -d'-' -f2 | tr -d ' ')
    elapsed_time=$(echo "$result" | cut -d'-' -f1 | tr -d ' ')
    
    echo "  Result: $elapsed_time ms, $match_count matches"
    
    if [ -n "$expected_matches" ] && [ "$match_count" != "$expected_matches" ]; then
        echo -e "  ${RED}FAILED: Expected $expected_matches matches, got $match_count${NC}"
        return 1
    else
        echo -e "  ${GREEN}PASSED${NC}"
        return 0
    fi
}

# Check if the program exists
program_found=false
if [ -f "../bin/benchmark" ]; then
    program_found=true
fi

if [ "$program_found" = false ]; then
    echo -e "${RED}FAILED: Java benchmark program not found${NC}"
    echo "Please run 'make all' first to compile the program."
    echo "Expected location: ../bin/benchmark"
    exit 1
fi
echo -e "${GREEN}Found Java benchmark program${NC}"
echo

# Test cases
passed=0
total=0

# Test 1: Simple word matching (partial match)
# Regex: "cat" -> base64: Y2F0
echo "--- Test Cases ---"
if run_test "Simple word match (partial)" "Y2F0" "simple_test.txt" "0"; then
    ((passed++))
fi
((total++))
echo

# Test 2: Email pattern matching (partial match)
# Regex: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" -> base64: W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==
if run_test "Email pattern match (partial)" "W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==" "test_data.txt" "0"; then
    ((passed++))
fi
((total++))
echo

# Test 3: Digit pattern matching (partial match)
# Regex: "\d+" -> base64: XGQr
if run_test "Digit pattern match (partial)" "XGQr" "test_data.txt" "0"; then
    ((passed++))
fi
((total++))
echo

# Test 4: Full match test
# Regex: "hello world" -> base64: aGVsbG8gd29ybGQ=
if run_test "Full match test" "aGVsbG8gd29ybGQ=" "full_match_test.txt" "1" "1"; then
    ((passed++))
fi
((total++))
echo

# Test 5: Full match test (should fail)
# Regex: "hello" -> base64: aGVsbG8=
if run_test "Full match test (should fail)" "aGVsbG8=" "full_match_test.txt" "1" "0"; then
    ((passed++))
fi
((total++))
echo

# Test 6: Word boundary test
# Regex: "\bcat\b" -> base64: XGJjYXRcYg==
if run_test "Word boundary test" "XGJjYXRcYg==" "simple_test.txt" "0"; then
    ((passed++))
fi
((total++))
echo

# Summary
echo "=== Test Summary ==="
echo "Passed: $passed/$total"
if [ $passed -eq $total ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi 