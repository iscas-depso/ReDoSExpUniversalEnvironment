#!/usr/bin/env python3
"""
GREWIA ReDoS Attack String Generator - Python Wrapper
Follows the program contract specified in the project guidelines.
"""

import sys
import subprocess
import os
import json
import base64
import tempfile
import time

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run.py <base64_regex> <output_json_file>")
        print("  base64_regex: Base64 encoded regex pattern")
        print("  output_json_file: Path to output JSON file")
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    output_json_file = sys.argv[2]
    
    # Default parameters for GREWIA
    # These can be made configurable if needed
    output_directory = tempfile.mkdtemp()  # Temporary directory for GREWIA's output
    attack_string_length = "100000"        # 100KB attack string length
    simplified_mode_on = "1"               # Generate a single attack string
    decremental_on = "0"                   # Decremental method off
    matching_function = "1"                # Target partial match
    regex_engine = "Java"                  # Default regex engine
    
    # Path to GREWIA executable
    grewia_exe = os.path.join(os.path.dirname(__file__), "build", "GREWIA")
    
    # Check if GREWIA executable exists
    if not os.path.exists(grewia_exe):
        # Create error output
        error_result = {
            "elapsed_ms": "0",
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": -1
        }
        with open(output_json_file, 'w') as f:
            json.dump(error_result, f, indent=2)
        print(f"Error: GREWIA executable not found at {grewia_exe}")
        print("Please build GREWIA first by running: cd build && cmake .. && make")
        sys.exit(1)
    
    try:
        # Run GREWIA with the specified parameters
        cmd = [
            grewia_exe,
            base64_regex,
            output_json_file,
            output_directory,
            attack_string_length,
            simplified_mode_on,
            decremental_on,
            matching_function,
            regex_engine
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        end_time = time.time()
        
        # Check if GREWIA created the output file
        if not os.path.exists(output_json_file):
            # Create fallback output if GREWIA didn't create the file
            fallback_result = {
                "elapsed_ms": str(int((end_time - start_time) * 1000)),
                "is_redos": False,
                "prefix": "",
                "infix": "",
                "suffix": "",
                "repeat_times": -1
            }
            with open(output_json_file, 'w') as f:
                json.dump(fallback_result, f, indent=2)
        
        # Print GREWIA's stdout/stderr if any
        if result.stdout:
            print("GREWIA output:", result.stdout)
        if result.stderr:
            print("GREWIA errors:", result.stderr, file=sys.stderr)
            
        # Clean up temporary directory
        try:
            os.rmdir(output_directory)
        except:
            pass  # Ignore cleanup errors
            
    except subprocess.TimeoutExpired:
        # Handle timeout
        timeout_result = {
            "elapsed_ms": "300000",  # 5 minutes
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": -1
        }
        with open(output_json_file, 'w') as f:
            json.dump(timeout_result, f, indent=2)
        print("Error: GREWIA execution timed out after 5 minutes")
        sys.exit(1)
        
    except Exception as e:
        # Handle other errors
        error_result = {
            "elapsed_ms": "0",
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": -1
        }
        with open(output_json_file, 'w') as f:
            json.dump(error_result, f, indent=2)
        print(f"Error running GREWIA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 