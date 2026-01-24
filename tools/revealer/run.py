#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - Revealer
Entry point script that follows the project contract.
"""

import sys
import subprocess
import json
import time
import os
import base64
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]

    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    jar_path = script_dir / "Revealer.jar"

    if not jar_path.exists():
        print(f"Error: revealer not found at {jar_path}", file=sys.stderr)
        sys.exit(1)

    try:
        raw_regex = base64.b64decode(base64_regex).decode("utf-8")
        # Record start time
        start_time = time.time()

        # Call the modified Java program with ID parameter and enable-preview flag
        result = subprocess.run(
            ["/usr/lib/jvm/java-8-openjdk-amd64/bin/java", "-jar", str(jar_path)],
            input=raw_regex,
            capture_output=True,
            text=True,
            timeout=1200,
        )

        # Record end time
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)

        # Parse the Java program output
        if result.returncode != 0:
            output_json = {
                "elapsed_ms": elapsed_ms,
                "is_redos": False,
                "error": result.stderr,
            }
        else:
            try:
                java_output = json.loads(result.stdout)
                print("java_output", java_output)
                output_json = convert_java_output_to_contract(java_output, elapsed_ms)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as not ReDoS
                output_json = {
                    "elapsed_ms": elapsed_ms,
                    "is_redos": False,
                    "error": result.stderr,
                    "stdout": result.stdout,
                }

        # Write output to file
        with open(output_file_path, "w") as f:
            json.dump(output_json, f, indent=2)

    except subprocess.TimeoutExpired:
        output_json = {
            "elapsed_ms": 600000,  # 10 minutes timeout
            "is_redos": False,
            "error": "Timeout",
            "stdout": result.stdout,
        }
        with open(output_file_path, "w") as f:
            json.dump(output_json, f, indent=2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        output_json = {
            "elapsed_ms": 0,
            "is_redos": False,
            "error": str(e),
            "stdout": result.stdout,
        }
        with open(output_file_path, "w") as f:
            json.dump(output_json, f, indent=2)


def convert_java_output_to_contract(java_output, elapsed_ms):
    """Convert Java output to the required contract format"""

    # Default output
    output = {"elapsed_ms": elapsed_ms, "is_redos": False}

    # Check if vulnerable
    if java_output.get("pump") != "None":
        output["is_redos"] = True

        prefix_b64 = base64.b64encode(
            java_output.get("prefix", "").encode("utf-8")
        ).decode("utf-8")
        infix_b64 = base64.b64encode(
            java_output.get("pump", "").encode("utf-8")
        ).decode("utf-8")
        suffix_b64 = base64.b64encode(
            java_output.get("suffix", "").encode("utf-8")
        ).decode("utf-8")
        repeat_times = -1

        # Use the extracted components
        output.update(
            {
                "prefix": prefix_b64,
                "infix": infix_b64,
                "suffix": suffix_b64,
                "repeat_times": repeat_times,
            }
        )

    return output


if __name__ == "__main__":
    main()
