#!/usr/bin/env python3
"""
ReDoSHunter tool wrapper script.
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 600
TIMEOUT_EXIT_CODE = 124


def load_timeout_seconds():
    try:
        timeout_seconds = int(os.environ.get("TOOL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout_seconds if timeout_seconds > 0 else DEFAULT_TIMEOUT_SECONDS


def build_failure(elapsed_ms, error_type, message, **extra):
    error = {
        "type": error_type,
        "message": message,
    }
    for key, value in extra.items():
        if value is not None:
            error[key] = value
    return {
        "elapsed_ms": elapsed_ms,
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": -1,
        "error": error,
    }


def classify_return_code(return_code):
    if return_code is None or return_code == 0:
        return ("tool_exception", None)
    if return_code < 0:
        return ("tool_exception", f"ReDoSHunter terminated by signal {-return_code}.")
    return ("child_exit_nonzero", "ReDoSHunter exited with a non-zero status.")


def decode_base64_regex(base64_regex):
    return base64.b64decode(base64_regex).decode("utf-8")


def encode_to_base64(text):
    if text is None:
        return ""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def parse_redoshunter_output(redoshunter_data, elapsed_ms):
    result = {
        "elapsed_ms": elapsed_ms,
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": -1,
    }

    if not isinstance(redoshunter_data, list):
        raise ValueError("ReDoSHunter output must be a JSON array.")

    for item in redoshunter_data:
        attacks = item.get("attackArrayList") if isinstance(item, dict) else None
        if not attacks:
            continue
        attack = attacks[0]
        result["is_redos"] = True
        result["prefix"] = encode_to_base64(attack.get("prefix", ""))
        result["infix"] = encode_to_base64(attack.get("infix", ""))
        result["suffix"] = encode_to_base64(attack.get("suffix", ""))
        repeat_times = attack.get("repeatTimes", -1)
        result["repeat_times"] = int(repeat_times) if repeat_times != -1 else -1
        break

    return result


def run_redoshunter(regex):
    jar_path = Path(__file__).parent / "ReDoSHunter.jar"
    if not jar_path.exists():
        return (build_failure(0, "tool_exception", f"ReDoSHunter JAR not found at {jar_path}"), 1)

    timeout_seconds = load_timeout_seconds()
    java_home = os.environ.get("JAVA_HOME")
    java_cmd = Path(java_home) / "bin" / "java" if java_home else Path("java")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(regex + "\n")
        input_file = tmp_file.name
    output_dir = tempfile.mkdtemp()
    start_time = time.time()

    try:
        result = subprocess.run(
            [str(java_cmd), "-jar", str(jar_path), os.path.dirname(input_file), os.path.basename(input_file), output_dir],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        output_files = list(Path(output_dir).glob("*.json"))

        if result.returncode != 0:
            error_type, default_message = classify_return_code(result.returncode)
            return (
                build_failure(
                    elapsed_ms,
                    error_type,
                    default_message,
                    returnValue=result.returncode,
                    stdout=result.stdout[-4000:] if result.stdout else "",
                    stderr=result.stderr[-4000:] if result.stderr else "",
                ),
                result.returncode or 1,
            )

        if output_files:
            with open(output_files[0], "r", encoding="utf-8") as handle:
                redoshunter_output = json.load(handle)
            return (parse_redoshunter_output(redoshunter_output, elapsed_ms), 0)

        return ({
            "elapsed_ms": elapsed_ms,
            "is_redos": False,
            "prefix": "",
            "infix": "",
            "suffix": "",
            "repeat_times": -1,
        }, 0)
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return (
            build_failure(
                elapsed_ms,
                "timeout",
                f"ReDoSHunter timed out after {timeout_seconds} seconds.",
                returnValue=TIMEOUT_EXIT_CODE,
            ),
            TIMEOUT_EXIT_CODE,
        )
    except Exception as error:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return (build_failure(elapsed_ms, "tool_exception", str(error)), 1)
    finally:
        try:
            os.unlink(input_file)
        except OSError:
            pass
        shutil.rmtree(output_dir, ignore_errors=True)


def main():
    start_time = time.time()
    if len(sys.argv) != 3:
        print("Usage: python3 run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file = sys.argv[2]

    try:
        regex = decode_base64_regex(base64_regex)
        result, exit_code = run_redoshunter(regex)
    except Exception as error:
        result = build_failure(int((time.time() - start_time) * 1000), "tool_exception", str(error))
        exit_code = 1

    result["elapsed_ms"] = int((time.time() - start_time) * 1000)
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
