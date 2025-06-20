#!/usr/bin/awk -f

# Base64 decoding using system base64 command
function base64_decode(input) {
    cmd = "echo '" input "' | base64 -d"
    cmd | getline result
    close(cmd)
    return result
}

# Read entire file into a string
function read_file(filename,    content, line) {
    content = ""
    while ((getline line < filename) > 0) {
        if (content == "") {
            content = line
        } else {
            content = content "\n" line
        }
    }
    close(filename)
    return content
}

# Get high precision time in milliseconds
function get_time_ms() {
    "date +%s.%6N" | getline time_str
    close("date +%s.%6N")
    return time_str * 1000
}

# Measure regex matching
function measure(data, pattern, full_match,    start_time, end_time, elapsed, match_count, line) {
    start_time = get_time_ms()
    match_count = 0
    
    if (full_match) {
        # Full match: entire text must match the regex
        full_pattern = "^" pattern "$"
        if (match(data, full_pattern)) {
            # Check if the match spans the entire string
            if (RSTART == 1 && RLENGTH == length(data)) {
                match_count = 1
            }
        }
    } else {
        # Partial match: count all matches across entire text
        temp_data = data
        while (match(temp_data, pattern)) {
            match_count++
            # Move past the matched portion to find next match
            if (RLENGTH > 0) {
                temp_data = substr(temp_data, RSTART + RLENGTH)
            } else {
                # Handle zero-length matches to prevent infinite loop
                temp_data = substr(temp_data, RSTART + 1)
            }
            if (length(temp_data) == 0) break
        }
    }
    
    end_time = get_time_ms()
    elapsed = end_time - start_time
    
    printf "%.6f - %d\n", elapsed, match_count
}

BEGIN {
    # Check arguments
    if (ARGC != 4) {
        print "Usage: " ARGV[0] " <base64_regex> <filename> <match_mode>" > "/dev/stderr"
        print "  base64_regex: Base64-encoded regular expression" > "/dev/stderr"
        print "  filename: Path to the file containing text to match" > "/dev/stderr"
        print "  match_mode: 1 for full match, 0 for partial match" > "/dev/stderr"
        exit 1
    }
    
    base64_regex = ARGV[1]
    filename = ARGV[2]
    match_mode = ARGV[3]
    
    # Validate match mode
    if (match_mode != "0" && match_mode != "1") {
        print "Error: match_mode must be 0 or 1" > "/dev/stderr"
        exit 1
    }
    
    # Decode base64 regex
    regex = base64_decode(base64_regex)
    if (regex == "") {
        print "Error: Failed to decode base64 regex" > "/dev/stderr"
        exit 1
    }
    
    # Read file content
    data = read_file(filename)
    if (data == "") {
        print "Error: Failed to read file or file is empty" > "/dev/stderr"
        exit 1
    }
    
    # Measure and output results
    measure(data, regex, match_mode == "1")
    
    exit 0
} 