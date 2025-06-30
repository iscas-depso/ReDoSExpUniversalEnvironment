#!/usr/bin/env python3
"""
ReDoSHunter tool wrapper script
Conforms to the project's program contract for ReDoS attack string generation tools.

Program Contract:
Args: 1. Base64 regex 2. output file path
Output: JSON file with format:
{
  "elapsed_ms": "elapsed_ms",
  "is_redos": true or false,
  "prefix": "a base64 encoded prefix of attack string",
  "infix": "a base64 encoded infix of attack string", 
  "suffix": "a base64 encoded suffix of attack string",
  "repeat_times": "the repeat times of the infix in the attack string which recommended by the tool, if the tool does not recommend, set it to -1"
}
"""

import sys
import os
import json
import base64
import subprocess
import tempfile
import time
from pathlib import Path

def decode_base64_regex(base64_regex):
    """Decode base64 encoded regex string"""
    try:
        return base64.b64decode(base64_regex).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decode base64 regex: {e}")

def encode_to_base64(text):
    """Encode text to base64"""
    if text is None:
        return ""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def run_redoshunter(regex, timeout=1200):
    """Run ReDoSHunter Java tool on the given regex"""
    jar_path = Path(__file__).parent / "ReDoSHunter.jar"
    
    if not jar_path.exists():
        raise FileNotFoundError(f"ReDoSHunter.jar not found at {jar_path}")
    
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(regex + '\n')
        input_file = tmp_file.name
    
    # Create temporary output directory
    output_dir = tempfile.mkdtemp()
    
    try:
        # Run ReDoSHunter with Java 8
        java8_path = '/usr/lib/jvm/java-8-openjdk-amd64/bin/java'
        cmd = [
            java8_path, '-jar', str(jar_path),
            os.path.dirname(input_file),
            os.path.basename(input_file),
            output_dir
        ]
        
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Check for output files
        output_files = list(Path(output_dir).glob('*.json'))
        
        if result.returncode == 0 and output_files:
            # Parse ReDoSHunter output
            with open(output_files[0], 'r') as f:
                redoshunter_output = json.load(f)
            return parse_redoshunter_output(redoshunter_output, elapsed_ms)
        else:
            # No ReDoS detected or error occurred
            return {
                "elapsed_ms": str(elapsed_ms),
                "is_redos": False,
                "error": result.stderr,
                "stdout": result.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {
            "elapsed_ms": str(timeout * 1000),
            "is_redos": False,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "elapsed_ms": "0",
            "is_redos": False,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            os.unlink(input_file)
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        except:
            pass

def parse_redoshunter_output(redoshunter_data, elapsed_ms):
    """Parse ReDoSHunter output and convert to project format"""
    result = {
        "elapsed_ms": str(elapsed_ms),
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": "-1"
    }
    
    try:
        # ReDoSHunter output is a list of results
        if isinstance(redoshunter_data, list) and len(redoshunter_data) > 0:
            for item in redoshunter_data:
                if 'attackArrayList' in item and len(item['attackArrayList']) > 0:
                    # Found a ReDoS vulnerability
                    attack = item['attackArrayList'][0]  # Use first attack
                    
                    result["is_redos"] = True
                    result["prefix"] = encode_to_base64(attack.get('prefix', ''))
                    result["infix"] = encode_to_base64(attack.get('infix', ''))
                    result["suffix"] = encode_to_base64(attack.get('suffix', ''))
                    
                    # Get actual repeat times from ReDoSHunter
                    repeat_times = attack.get('repeatTimes', -1)
                    result["repeat_times"] = str(repeat_times)
                    
                    break
    except Exception as e:
        # If parsing fails, return non-ReDoS result
        pass
    
    return result

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # Decode the regex
        regex = decode_base64_regex(base64_regex)
        
        # Run ReDoSHunter
        result = run_redoshunter(regex)
        
        # Write output
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
    except Exception as e:
        # On any error, output a non-ReDoS result
        error_result = {
            "elapsed_ms": "0",
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": "-1"
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(error_result, f, indent=2)
        except:
            pass
        
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 