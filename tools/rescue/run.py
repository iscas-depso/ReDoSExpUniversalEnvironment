#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - ReScue
Entry point script that follows the project contract.
"""

import sys
import subprocess
import json
import time
import base64
import os
import re
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]
    
    try:
        # Decode the base64 regex
        regex_bytes = base64.b64decode(base64_regex)
        regex_pattern = regex_bytes.decode('utf-8')
        
        # Record start time
        start_time = time.time()
        
        # Analyze the regex using ReScue
        output_json = analyze_regex(regex_pattern)
        
        # Record end time
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        output_json["elapsed_ms"] = elapsed_ms
        
        # Write output to file
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f, indent=2)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # In case of error, return a safe default
        output_json = {
            "elapsed_ms": 0,
            "is_redos": False
        }
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f, indent=2)

def analyze_regex(pattern):
    """Analyze a regex pattern for ReDoS vulnerabilities using ReScue"""
    
    # Default output
    output = {
        "elapsed_ms": 0,  # Will be set by main()
        "is_redos": False
    }
    
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Check if the JAR file exists
        jar_pattern = script_dir / "target" / "ReScue-0.0.1-SNAPSHOT.jar"
        
        if not jar_pattern.exists():
            print(f"Error: JAR file not found at {jar_pattern}", file=sys.stderr)
            return output
        
        # Run ReScue analysis
        # Use quiet mode to avoid interactive prompts
        cmd = [
            "java", "-jar", str(jar_pattern),
            "--quiet",
            "--maxLength", "64",
            "--generation", "50",  # Reduced for faster execution
            "--popSize", "50",     # Reduced for faster execution
            "--crossPossibility", "10",
            "--mutatePossibility", "10"
        ]
        
        # Provide the regex as input through stdin
        result = subprocess.run(cmd, 
                              input=pattern, 
                              text=True,
                              capture_output=True, 
                              timeout=120)  # 2 minute timeout
        
        if result.returncode != 0:
            print(f"ReScue analysis failed: {result.stderr}", file=sys.stderr)
            return output
        
        # Parse the output
        stdout_lines = result.stdout.strip().split('\n')
        if not stdout_lines:
            return output
        
        # Look for attack success indicators in the output
        attack_success = False
        attack_string = None
        
        for line in stdout_lines:
            line = line.strip()
            if "Attack success, attack string is:" in line:
                attack_success = True
            elif attack_success and line and not line.startswith("TIME:"):
                # The attack string is usually on the next line after "Attack success"
                attack_string = line
                break
        
        # Check if attack was successful
        if attack_success and attack_string:
            output["is_redos"] = True
            # For rescue, the attack string is not divided into prefix/infix/suffix
            # As per user's instruction: prefix and suffix empty, infix is the attack string, repeat_times = 1
            output.update({
                "prefix": base64.b64encode("".encode('utf-8')).decode('utf-8'),  # Empty prefix
                "infix": base64.b64encode(attack_string.encode('utf-8')).decode('utf-8'),  # Attack string as infix
                "suffix": base64.b64encode("".encode('utf-8')).decode('utf-8'),  # Empty suffix
                "repeat_times": 1  # Attack string used as-is, no repetition
            })
        else:
            # Check if it failed due to timeout or other reasons
            output["is_redos"] = False
    
    except subprocess.TimeoutExpired:
        print("ReScue analysis timed out", file=sys.stderr)
        output["is_redos"] = False
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        output["is_redos"] = False
    
    return output

if __name__ == "__main__":
    main() 