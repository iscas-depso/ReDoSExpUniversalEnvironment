#!/usr/bin/env php
<?php

function read_file($filename) {
    if (!file_exists($filename)) {
        fwrite(STDERR, "Error: Cannot open file $filename\n");
        exit(1);
    }
    
    $data = file_get_contents($filename);
    if ($data === false) {
        fwrite(STDERR, "Error: Failed to read file $filename\n");
        exit(1);
    }
    
    return $data;
}

function measure($data, $pattern, $full_match) {
    $start_time = microtime(true);
    
    $count = 0;
    
    // Prepare the regex pattern with proper delimiters
    $delimiter = '/';
    // Escape any delimiter characters in the pattern
    $escaped_pattern = str_replace($delimiter, '\\' . $delimiter, $pattern);
    
    if ($full_match) {
        // Full match: entire text must match the regex
        $full_pattern = $delimiter . '^' . $escaped_pattern . '$' . $delimiter . 's';
        if (preg_match($full_pattern, $data)) {
            $count = 1;
        }
    } else {
        // Partial match: count all matches in the text
        $partial_pattern = $delimiter . $escaped_pattern . $delimiter;
        $count = preg_match_all($partial_pattern, $data);
        if ($count === false) {
            $count = 0;
        }
    }
    
    $elapsed = (microtime(true) - $start_time) * 1000; // Convert to milliseconds
    
    printf("%.6f - %d\n", $elapsed, $count);
}

// Main program
if (count($argv) !== 4) {
    echo "Usage: {$argv[0]} <base64_regex> <filename> <match_mode>\n";
    echo "  base64_regex: Base64-encoded regular expression\n";
    echo "  filename: Path to the file containing text to match\n";
    echo "  match_mode: 1 for full match, 0 for partial match\n";
    exit(1);
}

$base64_regex = $argv[1];
$filename = $argv[2];
$match_mode = $argv[3];

// Decode the base64 regex
$regex = base64_decode($base64_regex, true);
if ($regex === false) {
    fwrite(STDERR, "Error: Failed to decode base64 regex\n");
    exit(1);
}

// Validate match mode
if ($match_mode !== '0' && $match_mode !== '1') {
    fwrite(STDERR, "Error: match_mode must be 0 or 1\n");
    exit(1);
}

// Read file content
$data = read_file($filename);

// Measure and output results
measure($data, $regex, $match_mode === '1');

?>
