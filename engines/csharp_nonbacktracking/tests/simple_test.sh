#!/bin/bash

echo "=== Simple C# Non-Backtracking Benchmark Tests ==="

# Function to find and run the program
run_program() {
    if [ -f "../bin/benchmark" ]; then
        ../bin/benchmark "$@"
    elif [ -f "../bin/benchmark.exe" ]; then
        ../bin/benchmark.exe "$@"
    elif [ -f "../bin/Release/net7.0/benchmark" ]; then
        ../bin/Release/net7.0/benchmark "$@"
    elif [ -f "../bin/Release/net7.0/benchmark.exe" ]; then
        ../bin/Release/net7.0/benchmark.exe "$@"
    else
        echo "FAILED: C# Non-Backtracking benchmark program not found"
        echo "Please run 'make all' first to compile the program."
        return 1
    fi
}

# Check if the program exists
program_found=false
if [ -f "../bin/benchmark" ] || [ -f "../bin/benchmark.exe" ] || \
   [ -f "../bin/Release/net7.0/benchmark" ] || [ -f "../bin/Release/net7.0/benchmark.exe" ]; then
    program_found=true
fi

if [ "$program_found" = false ]; then
    echo "FAILED: C# Non-Backtracking benchmark program not found"
    echo "Please run 'make all' first to compile the program."
    exit 1
fi

echo "SUCCESS: Found C# Non-Backtracking benchmark program"
echo "Note: This implementation uses .NET's non-backtracking regex engine"

# Test 1: Simple pattern match
echo ""
echo "Test 1: Simple pattern matching"
echo "Input: 'cat' pattern in simple_test.txt"
echo "Command: benchmark Y2F0 simple_test.txt 0"
run_program Y2F0 simple_test.txt 0
echo ""

# Test 2: Email pattern match
echo "Test 2: Email pattern matching"
echo "Input: Email regex in test_data.txt"
echo "Command: benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== test_data.txt 0"
run_program W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== test_data.txt 0
echo ""

# Test 3: Full match test
echo "Test 3: Full match test"
echo "Input: 'hello world' pattern in full_match_test.txt"
echo "Command: benchmark aGVsbG8gd29ybGQ= full_match_test.txt 1"
run_program aGVsbG8gd29ybGQ= full_match_test.txt 1
echo ""

echo "=== All tests completed ===" 