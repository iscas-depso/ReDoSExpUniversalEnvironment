#!/bin/bash

# Simple test script for RE2 benchmark

echo "Running simple RE2 benchmark test..."

# Check if benchmark exists
if [ ! -f "../bin/benchmark" ]; then
    echo "ERROR: benchmark program not found. Please run 'make all' first."
    exit 1
fi

# Test basic functionality
echo "Testing basic word match..."
result=$(../bin/benchmark "Y2F0" "simple_test.txt" "0" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✓ Basic test passed: $result"
else
    echo "✗ Basic test failed: $result"
    exit 1
fi

echo "Simple test completed successfully!" 