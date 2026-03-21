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
            "and print accepted records as a JSON document to stdout."
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


def json_error(message: str) -> None:
    json.dump({"status": "error", "message": message}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


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
        json_error(f"Input file not found: {input_path}")
        return 1

    if not Path(args.ere).exists():
        json_error(f"ere executable not found: {args.ere}")
        return 1

    accepted_records = []
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
            ere_pattern_b64 = base64.b64encode(ere_pattern.encode("utf-8")).decode("ascii")

            try:
                result = check_pattern(args.ere, ere_pattern, args.timeout)
            except subprocess.TimeoutExpired:
                timeout_lines.append(line_number)
                rejected_count += 1
                continue

            if result.returncode == 0:
                accepted_record = dict(record)
                accepted_record.update(
                    {
                        "line": line_number,
                        "ere_pattern": ere_pattern,
                        "ere_pattern_base64": ere_pattern_b64,
                        "ere_return_code": result.returncode,
                    }
                )
                accepted_records.append(accepted_record)
            else:
                rejected_count += 1

    output = {
        "status": "ok",
        "input_file": str(input_path),
        "ere_path": args.ere,
        "fullmatch_wrapped": use_fullmatch,
        "total_lines": total_lines,
        "processed_patterns": processed_patterns,
        "accepted_count": len(accepted_records),
        "rejected_count": rejected_count,
        "invalid_json_line_count": len(invalid_json_lines),
        "missing_pattern_count": len(missing_pattern_lines),
        "timeout_count": len(timeout_lines),
        "accepted_records": accepted_records,
    }

    if invalid_json_lines:
        output["invalid_json_lines"] = invalid_json_lines
    if missing_pattern_lines:
        output["missing_pattern_lines"] = missing_pattern_lines
    if timeout_lines:
        output["timeout_lines"] = timeout_lines

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
