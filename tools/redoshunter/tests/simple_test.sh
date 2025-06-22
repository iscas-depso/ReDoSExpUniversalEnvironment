#!/bin/bash

# Simple test script for ReDoSHunter tool

echo "Testing ReDoSHunter tool..."

# Test regex: (a+)+b (classic ReDoS pattern)
# Base64 encoded: KGErKStiFg==
TEST_REGEX_B64="KGErKSti"
OUTPUT_FILE="/tmp/redoshunter_test_output.json"

# Run the tool
python3 run.py "$TEST_REGEX_B64" "$OUTPUT_FILE"

# Check if output file was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Output file created successfully"
    echo "Output content:"
    cat "$OUTPUT_FILE"
    
    # Basic validation of JSON structure
    if python3 -c "import json; json.load(open('$OUTPUT_FILE'))" 2>/dev/null; then
        echo "✓ Valid JSON output"
    else
        echo "✗ Invalid JSON output"
        exit 1
    fi
    
    # Check required fields
    if python3 -c "
import json
data = json.load(open('$OUTPUT_FILE'))
required_fields = ['elapsed_ms', 'is_redos', 'prefix', 'infix', 'suffix', 'repeat_times']
missing = [f for f in required_fields if f not in data]
if missing:
    print('✗ Missing fields:', missing)
    exit(1)
else:
    print('✓ All required fields present')
" 2>/dev/null; then
        echo "✓ Test completed successfully"
    else
        echo "✗ Missing required fields"
        exit 1
    fi
    
    # Clean up
    rm -f "$OUTPUT_FILE"
    
else
    echo "✗ Output file was not created"
    exit 1
fi

echo "ReDoSHunter tool test passed!" 