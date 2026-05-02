#!/usr/bin/env python3

import base64
import os
import subprocess
import sys
import time
from pathlib import Path


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def decode_base64_regex(value: str) -> str:
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except Exception:
        fail("Error: Failed to decode base64 regex")


def has_nul_bytes(payload_path: Path) -> bool:
    return b"\x00" in payload_path.read_bytes()


def run_grep(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "LC_ALL": "C"},
        check=False,
    )


def count_partial_matches(payload_path: Path, pattern: str, contains_nul: bool) -> int:
    if contains_nul:
        result = run_grep(["grep", "-aPo", "--", pattern, str(payload_path)])
        if result.returncode == 1:
            return 0
        if result.returncode > 1:
            fail(result.stderr.decode("utf-8", errors="replace").strip() or "Error: grep failed")
        return len(result.stdout.splitlines())

    result = run_grep(["grep", "-aPzo", "--", pattern, str(payload_path)])
    if result.returncode == 1:
        return 0
    if result.returncode > 1:
        fail(result.stderr.decode("utf-8", errors="replace").strip() or "Error: grep failed")
    return result.stdout.count(b"\x00")


def check_full_match(payload_path: Path, pattern: str, contains_nul: bool) -> int:
    if contains_nul:
        fail("Error: grep full-match mode does not support payloads containing NUL bytes")

    result = run_grep(["grep", "-aPzqx", "--", pattern, str(payload_path)])
    if result.returncode == 0:
        return 1
    if result.returncode == 1:
        return 0
    fail(result.stderr.decode("utf-8", errors="replace").strip() or "Error: grep failed")


def main() -> None:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <base64_regex> <filename> <match_mode>", file=sys.stderr)
        print("  base64_regex: Base64-encoded regular expression", file=sys.stderr)
        print("  filename: Path to the file containing text to match", file=sys.stderr)
        print("  match_mode: 1 for full match, 0 for partial match", file=sys.stderr)
        raise SystemExit(1)

    regex = decode_base64_regex(sys.argv[1])
    payload_path = Path(sys.argv[2])
    match_mode = sys.argv[3]

    if match_mode not in {"0", "1"}:
        fail("Error: match_mode must be 0 or 1")
    if not payload_path.is_file():
        fail(f"Error: Cannot open file {payload_path}")

    contains_nul = has_nul_bytes(payload_path)
    start = time.perf_counter()
    if match_mode == "1":
        match_count = check_full_match(payload_path, regex, contains_nul)
    else:
        match_count = count_partial_matches(payload_path, regex, contains_nul)
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"{elapsed_ms:.6f} - {match_count}")


if __name__ == "__main__":
    main()
