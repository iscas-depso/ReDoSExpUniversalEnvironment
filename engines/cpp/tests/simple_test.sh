#!/bin/bash

echo "=== Simple C++ Benchmark Tests ==="

# Check if the program exists
if [ ! -f "../bin/benchmark" ]; then
    echo "FAILED: benchmark program not found in ../bin/benchmark"
    echo "Please run 'make all' first to compile the program."
    exit 1
fi

echo "SUCCESS: Found C++ benchmark program"

# Test 1: Simple pattern match
echo ""
echo "Test 1: Simple pattern matching"
echo "Input: 'cat' pattern in simple_test.txt"
echo "Command: ../bin/benchmark Y2F0 simple_test.txt 0"
../bin/benchmark Y2F0 simple_test.txt 0
echo ""

# Test 2: Email pattern match
echo "Test 2: Email pattern matching"
echo "Input: Email regex in test_data.txt"
echo "Command: ../bin/benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== test_data.txt 0"
../bin/benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== test_data.txt 0
echo ""

# Test 3: Full match test
echo "Test 3: Full match test"
echo "Input: 'hello world' pattern in full_match_test.txt"
echo "Command: ../bin/benchmark aGVsbG8gd29ybGQ= full_match_test.txt 1"
../bin/benchmark aGVsbG8gd29ybGQ= full_match_test.txt 1
echo ""

echo "=== All tests completed ===" 