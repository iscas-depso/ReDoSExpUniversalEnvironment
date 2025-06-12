#!/usr/bin/env python3

import sys
import re
import base64
import time

def read_file(filename):
    """Read file content and return as string."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read file {filename}: {e}", file=sys.stderr)
        sys.exit(1)

def measure(data, pattern, full_match):
    """Measure regex matching performance and count matches."""
    start_time = time.perf_counter()
    
    count = 0
    
    try:
        if full_match:
            # Full match: entire text must match the regex
            if re.fullmatch(pattern, data, re.DOTALL):
                count = 1
        else:
            # Partial match: count all matches in the text
            matches = re.findall(pattern, data)
            count = len(matches)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)
    
    elapsed = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
    
    print(f"{elapsed:.6f} - {count}")

def main():
    """Main program function."""
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <base64_regex> <filename> <match_mode>")
        print("  base64_regex: Base64-encoded regular expression")
        print("  filename: Path to the file containing text to match")
        print("  match_mode: 1 for full match, 0 for partial match")
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    filename = sys.argv[2]
    match_mode = sys.argv[3]
    
    # Decode the base64 regex
    try:
        regex_bytes = base64.b64decode(base64_regex, validate=True)
        regex = regex_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error: Failed to decode base64 regex: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate match mode
    if match_mode not in ['0', '1']:
        print("Error: match_mode must be 0 or 1", file=sys.stderr)
        sys.exit(1)
    
    # Read file content
    data = read_file(filename)
    
    # Measure and output results
    measure(data, regex, match_mode == '1')

if __name__ == "__main__":
    main()