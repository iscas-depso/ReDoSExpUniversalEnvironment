#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - RegexStatic
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
        
        # Analyze the regex using RegexStatic
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
    """Analyze a regex pattern for ReDoS vulnerabilities using RegexStatic"""
    
    # Default output
    output = {
        "elapsed_ms": 0,  # Will be set by main()
        "is_redos": False
    }
    
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Check if the JAR file exists
        jar_pattern = script_dir / "target" / "regex-static-analysis-1.0-SNAPSHOT.jar"
        deps_dir = script_dir / "target" / "dependency-jars"
        
        if not jar_pattern.exists():
            print(f"Error: JAR file not found at {jar_pattern}", file=sys.stderr)
            return output
        
        if not deps_dir.exists():
            print(f"Error: Dependencies directory not found at {deps_dir}", file=sys.stderr)
            return output
        
        # Run RegexStatic analysis
        # Use verbose mode to get exploit string details
        cmd = [
            "java", "-Xms2048m", 
            "-cp", f"{deps_dir}/*:{jar_pattern}", 
            "driver.Main",
            f"--regex={pattern}",
            "--verbose=true",
            "--construct-eda-exploit-string=true",
            "--construct-ida-exploit-string=true",
            "--timeout=30000"  # 30 second timeout
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"RegexStatic analysis failed: {result.stderr}", file=sys.stderr)
            return output
        
        # Parse the output
        stdout_lines = result.stdout.strip().split('\n')
        if not stdout_lines:
            return output
        
        # Look for vulnerability indicators in the output
        is_eda_vulnerable = False
        is_ida_vulnerable = False
        attack_prefix = ""
        attack_pump = ""
        attack_suffix = ""
        
        for line in stdout_lines:
            line = line.strip()
            # Look for EDA vulnerability indicators
            if "Contains EDA with:" in line:
                is_eda_vulnerable = True
            # Look for IDA vulnerability indicators (in summary line)  
            if "EDA:" in line and "IDA:" in line:
                # Check if EDA count is > 0 (format like "EDA:\t\t1/1")
                eda_match = re.search(r'EDA:\s*(\d+)/\d+', line)
                ida_match = re.search(r'IDA:\s*(\d+)/\d+', line)
                if eda_match and int(eda_match.group(1)) > 0:
                    is_eda_vulnerable = True
                if ida_match and int(ida_match.group(1)) > 0:
                    is_ida_vulnerable = True
            if "Prefix:" in line:
                # Extract prefix - simple approach to get quoted content
                prefix_match = re.search(r'"([^"]*)"', line)
                if prefix_match:
                    attack_prefix = prefix_match.group(1)
            if "Pump:" in line:
                # Extract pump (this is our infix) - simple approach to get quoted content
                pump_match = re.search(r'"([^"]*)"', line)
                if pump_match:
                    attack_pump = pump_match.group(1)
            if "Suffix:" in line:
                # Extract suffix - simple approach to get quoted content
                suffix_match = re.search(r'"([^"]*)"', line)
                if suffix_match:
                    attack_suffix = suffix_match.group(1)
        
        # Determine if it's ReDoS
        is_redos = is_eda_vulnerable or is_ida_vulnerable
        output["is_redos"] = is_redos
        
        if is_redos and (attack_prefix or attack_pump or attack_suffix):
            # Use the extracted attack components
            prefix = attack_prefix if attack_prefix else ""
            infix = attack_pump if attack_pump else "a"
            suffix = attack_suffix if attack_suffix else "x"
            
            # Calculate repeat times based on pump length (default to 1000)
            repeat_times = 1000
            if attack_pump:
                # For regexstatic, we recommend repeating the pump 1000 times
                repeat_times = 1000
            
            output.update({
                "prefix": base64.b64encode(prefix.encode('utf-8')).decode('utf-8'),
                "infix": base64.b64encode(infix.encode('utf-8')).decode('utf-8'),
                "suffix": base64.b64encode(suffix.encode('utf-8')).decode('utf-8'),
                "repeat_times": repeat_times
            })
        elif is_redos:
            # If vulnerable but no attack details, provide a basic one
            output.update({
                "prefix": base64.b64encode("".encode('utf-8')).decode('utf-8'),
                "infix": base64.b64encode("a".encode('utf-8')).decode('utf-8'),
                "suffix": base64.b64encode("x".encode('utf-8')).decode('utf-8'),
                "repeat_times": 1000
            })
    
    except subprocess.TimeoutExpired:
        print("RegexStatic analysis timed out", file=sys.stderr)
        output["is_redos"] = False
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        output["is_redos"] = False
    
    return output

def parse_attack_string(attack_string):
    """Parse the attack string from RegexStatic output to extract components"""
    
    # Default values
    prefix = ""
    infix = "a"
    suffix = "x"
    repeat_times = 1000
    
    try:
        # RegexStatic often outputs strings like "aaa...aaa" + "x" or similar patterns
        # Try to identify the repeating pattern
        
        # Look for patterns like 'a' repeated multiple times followed by a different character
        if len(attack_string) > 2:
            # Find the most common character (likely the repeating one)
            char_counts = {}
            for char in attack_string:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            # Find the most frequent character
            most_frequent_char = max(char_counts, key=char_counts.get)
            
            # Check if the string ends with a different character
            if attack_string[-1] != most_frequent_char:
                suffix = attack_string[-1]
                # The rest is mostly the repeating character
                main_part = attack_string[:-1]
                
                # Find where the repeating part starts
                prefix_end = 0
                while prefix_end < len(main_part) and main_part[prefix_end] != most_frequent_char:
                    prefix_end += 1
                
                if prefix_end > 0:
                    prefix = main_part[:prefix_end]
                
                infix = most_frequent_char
                repeat_times = char_counts[most_frequent_char]
            else:
                # All characters are the same, treat as infix
                infix = most_frequent_char
                repeat_times = len(attack_string)
        else:
            # Short string, treat as infix
            infix = attack_string if attack_string else "a"
            repeat_times = len(attack_string) if attack_string else 1000
    
    except Exception as e:
        print(f"Error parsing attack string: {e}", file=sys.stderr)
        # Return defaults
        pass
    
    return prefix, infix, suffix, repeat_times

if __name__ == "__main__":
    main() 