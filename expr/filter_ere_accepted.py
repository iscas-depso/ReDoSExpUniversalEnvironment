#!/usr/bin/env python3

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sequentially run `ere detect -bv` on each pattern in a JSONL file "
            "and print each accepted input line unchanged to stdout."
        )
    )
    parser.add_argument(
        "--input",
        default="/app/expr/data/cve414_with_metadata_no_slq_only.jsonl",
        help="Path to the input JSONL file inside the container.",
    )
    parser.add_argument(
        "--ere",
        default="/app/tools/ere/ere",
        help="Path to the ere executable inside the container.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for each `ere detect -bv` invocation.",
    )
    parser.add_argument(
        "--fullmatch",
        action="store_true",
        help="Wrap the pattern as ^(?:pattern)$ before passing it to ere.",
    )
    return parser.parse_args()


def build_ere_pattern(pattern: str, use_fullmatch: bool) -> str:
    if use_fullmatch:
        return f"^(?:{pattern})$"
    return pattern


def check_pattern(ere_path: str, pattern: str, timeout: float) -> subprocess.CompletedProcess[str]:
    pattern_b64 = base64.b64encode(pattern.encode("utf-8")).decode("ascii")
    return subprocess.run(
        [ere_path, "detect", "-bv"],
        input=pattern_b64,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    use_fullmatch = args.fullmatch

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    if not Path(args.ere).exists():
        print(f"ere executable not found: {args.ere}", file=sys.stderr)
        return 1

    invalid_json_lines = []
    missing_pattern_lines = []
    timeout_lines = []

    total_lines = 0
    processed_patterns = 0
    rejected_count = 0

    with input_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            total_lines += 1
            stripped = raw_line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                invalid_json_lines.append(
                    {"line": line_number, "error": str(exc)}
                )
                continue

            pattern = record.get("pattern")
            if not isinstance(pattern, str):
                missing_pattern_lines.append(line_number)
                continue

            processed_patterns += 1
            ere_pattern = build_ere_pattern(pattern, use_fullmatch)
            try:
                result = check_pattern(args.ere, ere_pattern, args.timeout)
            except subprocess.TimeoutExpired:
                timeout_lines.append(line_number)
                rejected_count += 1
                continue

            if result.returncode == 0:
                sys.stdout.write(raw_line)
                if not raw_line.endswith("\n"):
                    sys.stdout.write("\n")
            else:
                rejected_count += 1

    print(
        (
            f"Finished filtering {input_path}: total_lines={total_lines}, "
            f"processed_patterns={processed_patterns}, "
            f"rejected_count={rejected_count}, invalid_json_line_count={len(invalid_json_lines)}, "
            f"missing_pattern_count={len(missing_pattern_lines)}, timeout_count={len(timeout_lines)}, "
            f"fullmatch_wrapped={use_fullmatch}"
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
