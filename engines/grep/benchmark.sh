#!/bin/bash

# Grep Benchmark Script
# Implements the 3-argument interface: base64_regex filename match_mode

# Function to decode base64
decode_base64() {
    echo "$1" | base64 -d 2>/dev/null
}

# Function to read file content
read_file() {
    local filename="$1"
    if [ ! -f "$filename" ]; then
        echo "Error: Cannot open file $filename" >&2
        exit 1
    fi
    cat "$filename"
}

# Function to get high precision time in nanoseconds
get_time_ns() {
    date +%s%N
}

# Function to measure grep performance
measure_grep() {
    local data="$1"
    local pattern="$2"
    local full_match="$3"
    local start_time end_time elapsed match_count
    
    start_time=$(get_time_ns)
    
    if [ "$full_match" = "1" ]; then
        # Full match: entire text must match the regex
        # Use grep with -x flag for full line match and check if the pattern matches the whole text
        if echo "$data" | grep -Pqx "$pattern"; then
            match_count=1
        else
            match_count=0
        fi
    else
        # Partial match: count all matches using grep -o to find all occurrences
        match_count=$(echo "$data" | grep -Po "$pattern" 2>/dev/null | wc -l)
        # If PCRE fails, fall back to basic regex
        if [ $? -ne 0 ]; then
            match_count=$(echo "$data" | grep -Eo "$pattern" 2>/dev/null | wc -l)
        fi
    fi
    
    end_time=$(get_time_ns)
    # Convert nanoseconds to milliseconds with 6 decimal places
    elapsed=$(awk "BEGIN {printf \"%.6f\", ($end_time - $start_time) / 1000000}")
    
    printf "%s - %d\n" "$elapsed" "$match_count"
}

# Main function
main() {
    # Check arguments
    if [ $# -ne 3 ]; then
        echo "Usage: $0 <base64_regex> <filename> <match_mode>" >&2
        echo "  base64_regex: Base64-encoded regular expression" >&2
        echo "  filename: Path to the file containing text to match" >&2
        echo "  match_mode: 1 for full match, 0 for partial match" >&2
        exit 1
    fi
    
    local base64_regex="$1"
    local filename="$2"
    local match_mode="$3"
    
    # Validate match mode
    if [ "$match_mode" != "0" ] && [ "$match_mode" != "1" ]; then
        echo "Error: match_mode must be 0 or 1" >&2
        exit 1
    fi
    
    # Decode base64 regex
    local regex
    regex=$(decode_base64 "$base64_regex")
    if [ -z "$regex" ]; then
        echo "Error: Failed to decode base64 regex" >&2
        exit 1
    fi
    
    # Read file content
    local data
    data=$(read_file "$filename")
    if [ -z "$data" ]; then
        echo "Error: Failed to read file or file is empty" >&2
        exit 1
    fi
    
    # Measure and output results
    measure_grep "$data" "$regex" "$match_mode"
}

# Run main function with all arguments
main "$@" 