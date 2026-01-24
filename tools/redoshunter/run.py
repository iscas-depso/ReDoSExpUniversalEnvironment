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
        return base64.b64decode(base64_regex).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decode base64 regex: {e}")


def encode_to_base64(text):
    """Encode text to base64"""
    if text is None:
        return ""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def run_redoshunter(regex, cpu_core=None, timeout=1200):
    """Run ReDoSHunter shaded JAR on the given regex"""
    jar_path = Path(__file__).parent / "ReDoSHunter.jar"
    if not jar_path.exists():
        raise FileNotFoundError(f"ReDoSHunter JAR not found at {jar_path}")

    java_home = os.environ.get("JAVA_HOME")
    java_cmd = Path(java_home) / "bin" / "java" if java_home else Path("java")
    java_cmd = str(java_cmd)

    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(regex + "\n")
        input_file = tmp_file.name

    # Create temporary output directory
    output_dir = tempfile.mkdtemp()

    try:
        cmd = [
            java_cmd,
            "-jar",
            str(jar_path),
            os.path.dirname(input_file),
            os.path.basename(input_file),
            output_dir,
        ]
        if cpu_core:
            cmd = ["taskset", "-c", str(cpu_core), *cmd]

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Check for output files
        output_files = list(Path(output_dir).glob("*.json"))

        if result.returncode == 0 and output_files:
            # Parse ReDoSHunter output
            with open(output_files[0], "r") as f:
                redoshunter_output = json.load(f)
            return parse_redoshunter_output(redoshunter_output, elapsed_ms)
        else:
            return {
                "elapsed_ms": elapsed_ms,
                "is_redos": False,
                "error": result.stderr,
                "stdout": result.stdout,
            }

    except subprocess.TimeoutExpired:
        return {"elapsed_ms": timeout * 1000, "is_redos": False, "error": "Timeout"}
    except Exception as e:
        return {"elapsed_ms": 0, "is_redos": False, "error": str(e)}
    finally:
        try:
            os.unlink(input_file)
        except OSError:
            pass
        import shutil

        shutil.rmtree(output_dir, ignore_errors=True)


def parse_redoshunter_output(redoshunter_data, elapsed_ms):
    """Parse ReDoSHunter output and convert to project format"""
    result = {
        "elapsed_ms": elapsed_ms,  # Must be a number per contract
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": -1,  # Must be a number per contract
    }

    try:
        # ReDoSHunter output is a list of results
        if isinstance(redoshunter_data, list) and len(redoshunter_data) > 0:
            for item in redoshunter_data:
                if "attackArrayList" in item and len(item["attackArrayList"]) > 0:
                    # Found a ReDoS vulnerability
                    attack = item["attackArrayList"][0]  # Use first attack

                    result["is_redos"] = True
                    result["prefix"] = encode_to_base64(attack.get("prefix", ""))
                    result["infix"] = encode_to_base64(attack.get("infix", ""))
                    result["suffix"] = encode_to_base64(attack.get("suffix", ""))

                    repeat_times = attack.get("repeatTimes", -1)
                    result["repeat_times"] = (
                        int(repeat_times) if repeat_times != -1 else -1
                    )

                    break
    except Exception as e:
        # If parsing fails, return non-ReDoS result
        pass

    return result


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python run.py <base64_regex> <output_file_path> <cpu_core>",
            file=sys.stderr,
        )
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file = sys.argv[2]
    cpu_core = sys.argv[3]

    try:
        # Decode the regex
        regex = decode_base64_regex(base64_regex)

        # Run ReDoSHunter
        result = run_redoshunter(regex, cpu_core=cpu_core)

        # Write output
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

    except Exception as e:
        error_result = {
            "elapsed_ms": 0,
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": -1,
            "error": str(e),
        }

        try:
            with open(output_file, "w") as f:
                json.dump(error_result, f, indent=2)
        except Exception as write_error:
            print(f"Failed to write output file: {write_error}", file=sys.stderr)

        print(f"Error: {e}", file=sys.stderr)
        # Don't exit with error code, just log the error
        # sys.exit(1)


if __name__ == "__main__":
    main()
