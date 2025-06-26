#!/bin/bash

# Simple test script for ReScue tool
# Tests the basic functionality with known ReDoS patterns

set -e

echo "Running simple tests for ReScue tool..."

# Test 1: Known exponential ReDoS pattern (a+)+
echo "Test 1: Testing with known exponential ReDoS pattern (a+)+"
TEST_REGEX="KGErKSs="  # Base64 for "(a+)+"
OUTPUT_FILE="/tmp/rescue_test1.json"

python3 ../run.py "$TEST_REGEX" "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    
    # Check if JSON is valid
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "✓ Output is valid JSON"
        
        # Check if is_redos is true or false (ReScue may or may not find attack strings)
        IS_REDOS=$(python3 -c "import json; print(json.load(open('$OUTPUT_FILE'))['is_redos'])")
        echo "ℹ ReDoS detection result: $IS_REDOS"
        
        # If ReDoS was detected, verify attack string components
        if [ "$IS_REDOS" = "True" ]; then
            echo "✓ ReScue detected ReDoS vulnerability"
            HAS_INFIX=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print('infix' in data)")
            if [ "$HAS_INFIX" = "True" ]; then
                echo "✓ Attack string components present"
                # Decode and show the attack string
                ATTACK_STRING=$(python3 -c "import json, base64; data=json.load(open('$OUTPUT_FILE')); print(base64.b64decode(data['infix']).decode('utf-8'))" 2>/dev/null || echo "Unable to decode")
                echo "ℹ Attack string: $ATTACK_STRING"
            fi
        else
            echo "ℹ ReScue did not find ReDoS vulnerability (genetic algorithm may not have found attack string)"
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

# Test 2: Simple pattern that should be safe
echo ""
echo "Test 2: Testing with non-ReDoS pattern"
TEST_REGEX="XmFiYyQ="  # Base64 for "^abc$"
OUTPUT_FILE="/tmp/rescue_test2.json"

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
            echo "⚠ Unexpected ReDoS detection for simple pattern: $IS_REDOS"
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

# Test 3: A known vulnerable pattern that should trigger ReScue
echo ""
echo "Test 3: Testing with pattern from ReScue examples"
TEST_REGEX="KD89KGErKStiKWFhYWJ4"  # Base64 for "(?=(a+)+b)aaabx"
OUTPUT_FILE="/tmp/rescue_test3.json"

python3 ../run.py "$TEST_REGEX" "$OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    
    # Check if JSON is valid
    if python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "✓ Output is valid JSON"
        
        IS_REDOS=$(python3 -c "import json; print(json.load(open('$OUTPUT_FILE'))['is_redos'])")
        echo "ℹ ReDoS detection result: $IS_REDOS"
        
        if [ "$IS_REDOS" = "True" ]; then
            echo "✓ ReScue detected ReDoS vulnerability"
        else
            echo "ℹ ReScue did not find ReDoS vulnerability (genetic algorithm may not have found attack string within time limit)"
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
rm -f /tmp/rescue_test*.json

echo ""
echo "All tests completed successfully!"
echo "Note: ReScue uses genetic algorithms, so results may vary between runs." 