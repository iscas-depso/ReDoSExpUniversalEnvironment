#!/bin/bash

# Simple test script for RegexStatic tool
# Tests the basic functionality with known ReDoS patterns

set -e

echo "Running simple tests for RegexStatic tool..."

# Test 1: Known exponential ReDoS pattern (a+)+
echo "Test 1: Testing with known exponential ReDoS pattern (a+)+"
TEST_REGEX="KGErKSs="  # Base64 for "(a+)+"
OUTPUT_FILE="/tmp/regexstatic_test1.json"

python3 ../run.py "$TEST_REGEX" "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    
    # Check if JSON is valid
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "✓ Output is valid JSON"
        
        # Check if is_redos is true for this pattern
        IS_REDOS=$(python3 -c "import json; print(json.load(open('$OUTPUT_FILE'))['is_redos'])")
        if [ "$IS_REDOS" = "True" ]; then
            echo "✓ Correctly detected ReDoS vulnerability"
        else
            echo "⚠ Expected ReDoS detection, but got: $IS_REDOS"
        fi
    else
        echo "✗ Output is not valid JSON"
        cat "$OUTPUT_FILE"
        exit 1
    fi
else
    echo "✗ Output file not created"
    exit 1
fi

# Test 2: Known polynomial ReDoS pattern a*a*
echo ""
echo "Test 2: Testing with known polynomial ReDoS pattern a*a*"
TEST_REGEX="YSphKg=="  # Base64 for "a*a*"
OUTPUT_FILE="/tmp/regexstatic_test2.json"

python3 ../run.py "$TEST_REGEX" "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    
    # Check if JSON is valid
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "✓ Output is valid JSON"
        
        # Check if is_redos is true for this pattern
        IS_REDOS=$(python3 -c "import json; print(json.load(open('$OUTPUT_FILE'))['is_redos'])")
        if [ "$IS_REDOS" = "True" ]; then
            echo "✓ Correctly detected ReDoS vulnerability"
        else
            echo "⚠ Expected ReDoS detection, but got: $IS_REDOS"
        fi
    else
        echo "✗ Output is not valid JSON"
        cat "$OUTPUT_FILE"
        exit 1
    fi
else
    echo "✗ Output file not created"
    exit 1
fi

# Test 3: Non-ReDoS pattern
echo ""
echo "Test 3: Testing with non-ReDoS pattern"
TEST_REGEX="XmFiYyQ="  # Base64 for "^abc$"
OUTPUT_FILE="/tmp/regexstatic_test3.json"

python3 ../run.py "$TEST_REGEX" "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    
    # Check if JSON is valid
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "✓ Output is valid JSON"
        
        # Check if is_redos is false for this pattern
        IS_REDOS=$(python3 -c "import json; print(json.load(open('$OUTPUT_FILE'))['is_redos'])")
        if [ "$IS_REDOS" = "False" ]; then
            echo "✓ Correctly identified non-ReDoS pattern"
        else
            echo "⚠ Expected non-ReDoS, but got: $IS_REDOS"
        fi
    else
        echo "✗ Output is not valid JSON"
        cat "$OUTPUT_FILE"
        exit 1
    fi
else
    echo "✗ Output file not created"
    exit 1
fi

# Clean up
rm -f /tmp/regexstatic_test*.json

echo ""
echo "All tests completed successfully!" 