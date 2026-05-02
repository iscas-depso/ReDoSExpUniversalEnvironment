#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - Rengar
Entry point script that follows the project contract.
"""

import base64
import json
import os
import subprocess
import sys
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
        return ("tool_exception", f"Rengar terminated by signal {-return_code}.")
    return ("child_exit_nonzero", "Rengar exited with a non-zero status.")


def convert_java_output_to_contract(java_output, elapsed_ms):
    output = {
        "elapsed_ms": elapsed_ms,
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": -1,
    }

    if java_output.get("Status") != "Vulnerable":
        return output

    output["is_redos"] = True
    details = java_output.get("Details", [])
    if details:
        attack_detail = details[0]
        output.update({
            "prefix": attack_detail.get("Prefix", ""),
            "infix": attack_detail.get("Infix", ""),
            "suffix": attack_detail.get("Suffix", ""),
            "repeat_times": attack_detail.get("RecommendedRepeatTimes", -1)
        })
    else:
        output.update({
            "prefix": base64.b64encode(b"").decode("utf-8"),
            "infix": base64.b64encode(b"a").decode("utf-8"),
            "suffix": base64.b64encode(b"").decode("utf-8"),
            "repeat_times": -1
        })
    return output


def main():
    start_time = time.time()
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]
    script_dir = Path(__file__).parent
    jar_path = script_dir / "Rengar.jar"
    timeout_seconds = load_timeout_seconds()

    if not jar_path.exists():
        output_json = build_failure(0, "tool_exception", f"Rengar.jar not found at {jar_path}")
        with open(output_file_path, "w", encoding="utf-8") as handle:
            json.dump(output_json, handle, indent=2)
        sys.exit(1)

    java_bin = os.environ.get("JAVA_BIN", "/usr/lib/jvm/java-17-openjdk-amd64/bin/java")
    try:
        result = subprocess.run([
            java_bin, "--enable-preview", "-jar", str(jar_path),
            "-s", base64_regex,
            "-id", "1",
            "-q"
        ], capture_output=True, text=True, timeout=timeout_seconds)

        elapsed_ms = int((time.time() - start_time) * 1000)
        if result.returncode != 0:
            error_type, default_message = classify_return_code(result.returncode)
            output_json = build_failure(
                elapsed_ms,
                error_type,
                default_message,
                returnValue=result.returncode,
                stdout=result.stdout[-4000:] if result.stdout else "",
                stderr=result.stderr[-4000:] if result.stderr else "",
            )
            exit_code = result.returncode or 1
        else:
            try:
                java_output = json.loads(result.stdout.splitlines()[-1])
                output_json = convert_java_output_to_contract(java_output, elapsed_ms)
                exit_code = 0
            except (IndexError, json.JSONDecodeError) as error:
                output_json = build_failure(
                    elapsed_ms,
                    "tool_exception",
                    f"Failed to parse Rengar output: {error}",
                    stdout=result.stdout[-4000:] if result.stdout else "",
                    stderr=result.stderr[-4000:] if result.stderr else "",
                )
                exit_code = 1
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.time() - start_time) * 1000)
        output_json = build_failure(
            elapsed_ms,
            "timeout",
            f"Rengar timed out after {timeout_seconds} seconds.",
            returnValue=TIMEOUT_EXIT_CODE,
        )
        exit_code = TIMEOUT_EXIT_CODE
    except Exception as error:
        elapsed_ms = int((time.time() - start_time) * 1000)
        output_json = build_failure(elapsed_ms, "tool_exception", str(error))
        exit_code = 1

    output_json["elapsed_ms"] = int((time.time() - start_time) * 1000)
    with open(output_file_path, "w", encoding="utf-8") as handle:
        json.dump(output_json, handle, indent=2)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
