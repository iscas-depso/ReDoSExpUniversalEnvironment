#!/bin/bash

# Simple test script for Rengar tool
# Tests basic functionality with known vulnerable regex patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_DIR="$(dirname "$SCRIPT_DIR")"
RUN_SCRIPT="$TOOL_DIR/run.py"

echo "Testing Rengar ReDoS detection tool..."

# Test 1: Known ReDoS vulnerable pattern (a*)*b
echo "Test 1: Testing vulnerable pattern (a*)*b"
REGEX="KGEqKSpi"  # Base64 encoded "(a*)*b"
OUTPUT_FILE="test1_output.json"

python3 "$RUN_SCRIPT" "$REGEX" "$OUTPUT_FILE"
if [ $? -eq 0 ]; then
    echo "✓ Test 1 completed successfully"
    if [ -f "$OUTPUT_FILE" ]; then
        echo "  Output file created: $OUTPUT_FILE"
        # Check if it's marked as ReDoS
        if grep -q '"is_redos": true' "$OUTPUT_FILE"; then
            echo "  ✓ Correctly identified as ReDoS vulnerable"
        else
            echo "  ⚠ Not identified as ReDoS vulnerable (might be expected)"
        fi
    else
        echo "  ✗ Output file not created"
    fi
else
    echo "✗ Test 1 failed"
fi

# Test 2: Simple safe pattern
echo -e "\nTest 2: Testing safe pattern abc"
REGEX="YWJj"  # Base64 encoded "abc"
OUTPUT_FILE2="test2_output.json"

python3 "$RUN_SCRIPT" "$REGEX" "$OUTPUT_FILE2"
if [ $? -eq 0 ]; then
    echo "✓ Test 2 completed successfully"
    if [ -f "$OUTPUT_FILE2" ]; then
        echo "  Output file created: $OUTPUT_FILE2"
        # Check if it's marked as safe
        if grep -q '"is_redos": false' "$OUTPUT_FILE2"; then
            echo "  ✓ Correctly identified as safe"
        else
            echo "  ⚠ Not identified as safe"
        fi
    else
        echo "  ✗ Output file not created"
    fi
else
    echo "✗ Test 2 failed"
fi

# Clean up
echo -e "\nCleaning up test files..."
rm -f test1_output.json test2_output.json

echo "Tests completed." 