#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - ReScue
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
    raw_value = os.environ.get("TOOL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout_seconds = int(raw_value)
    except (TypeError, ValueError):
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
        return ("tool_exception", f"ReScue analysis terminated by signal {-return_code}.")
    return ("child_exit_nonzero", "ReScue analysis exited with a non-zero status.")


def analyze_regex(pattern):
    script_dir = Path(__file__).parent
    jar_pattern = script_dir / "target" / "ReScue-0.0.1-SNAPSHOT.jar"
    if not jar_pattern.exists():
        return (
            build_failure(0, "tool_exception", f"JAR file not found at {jar_pattern}"),
            1,
        )

    cmd = [
        "java", "-jar", str(jar_pattern),
        "--quiet",
        "--maxLength", "64",
        "--generation", "50",
        "--popSize", "50",
        "--crossPossibility", "10",
        "--mutatePossibility", "10"
    ]

    timeout_seconds = load_timeout_seconds()
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            input=pattern,
            text=True,
            capture_output=True,
            timeout=timeout_seconds
        )
        elapsed_ms = int((time.time() - start_time) * 1000)

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

        stdout_lines = result.stdout.strip().splitlines()
        attack_success = False
        attack_string = None
        for line in stdout_lines:
            line = line.strip()
            if "Attack success, attack string is:" in line:
                attack_success = True
            elif attack_success and line and not line.startswith("TIME:"):
                attack_string = line
                break

        if attack_success and attack_string:
            return ({
                "elapsed_ms": elapsed_ms,
                "is_redos": True,
                "prefix": base64.b64encode(b"").decode("utf-8"),
                "infix": base64.b64encode(attack_string.encode("utf-8")).decode("utf-8"),
                "suffix": base64.b64encode(b"").decode("utf-8"),
                "repeat_times": 1,
            }, 0)

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
                f"ReScue analysis timed out after {timeout_seconds} seconds.",
                returnValue=TIMEOUT_EXIT_CODE,
            ),
            TIMEOUT_EXIT_CODE,
        )
    except Exception as error:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return (build_failure(elapsed_ms, "tool_exception", str(error)), 1)


def main():
    start_time = time.time()
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]

    try:
        regex_pattern = base64.b64decode(base64_regex).decode("utf-8")
        output_json, exit_code = analyze_regex(regex_pattern)
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
