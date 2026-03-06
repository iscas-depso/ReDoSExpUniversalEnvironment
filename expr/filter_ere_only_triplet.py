#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

TARGET_ENGINES = {"java11", "nodejs14", "python"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter GT records where all three engines exist and each has successful_tools == ['ere']."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("expr/ground_truth/ground_truth_all_engines.jsonl"),
        help="Input JSONL file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("expr/ground_truth/ground_truth_ere_only_triplet.jsonl"),
        help="Output JSONL file",
    )
    return parser.parse_args()


def is_tools_ere_only(tools) -> bool:
    if not isinstance(tools, list):
        return False
    return len(tools) == 1 and set(tools) == {"ere"}


def record_matches(obj: dict) -> tuple[bool, str]:
    engines = obj.get("engines")
    if not isinstance(engines, list) or set(engines) != TARGET_ENGINES:
        return False, "skipped_engine_set"

    details = obj.get("engine_details")
    if not isinstance(details, dict) or not TARGET_ENGINES.issubset(set(details.keys())):
        return False, "skipped_missing_engine_details"

    for eng in TARGET_ENGINES:
        det = details.get(eng)
        if not isinstance(det, dict):
            return False, "skipped_missing_engine_details"
        tools = det.get("successful_tools")
        if not is_tools_ere_only(tools):
            return False, "skipped_tools_not_ere_only"

    return True, "matched"


def main() -> None:
    args = parse_args()

    counters = {
        "total_lines": 0,
        "parsed_ok": 0,
        "matched": 0,
        "skipped_invalid_json": 0,
        "skipped_engine_set": 0,
        "skipped_missing_engine_details": 0,
        "skipped_tools_not_ere_only": 0,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.input.open("r", encoding="utf-8") as fin, args.output.open(
        "w", encoding="utf-8"
    ) as fout:
        for raw in fin:
            counters["total_lines"] += 1
            line = raw.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                counters["skipped_invalid_json"] += 1
                continue

            counters["parsed_ok"] += 1
            ok, tag = record_matches(obj)
            counters[tag] += 1
            if ok:
                fout.write(json.dumps(obj, ensure_ascii=True) + "\n")

    print(
        " ".join(
            [
                f"total_lines={counters['total_lines']}",
                f"parsed_ok={counters['parsed_ok']}",
                f"matched={counters['matched']}",
                f"skipped_invalid_json={counters['skipped_invalid_json']}",
                f"skipped_engine_set={counters['skipped_engine_set']}",
                f"skipped_missing_engine_details={counters['skipped_missing_engine_details']}",
                f"skipped_tools_not_ere_only={counters['skipped_tools_not_ere_only']}",
            ]
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
