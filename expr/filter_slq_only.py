#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Filter out records whose Vul_Pattern is exactly ['SLQ'] "
            "from a JSONL file."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("expr/data/cve414_with_metadata.jsonl"),
        help="Path to the input JSONL file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("expr/data/cve414_with_metadata_no_slq_only.jsonl"),
        help="Path to the output JSONL file.",
    )
    return parser.parse_args()


def should_drop(record: dict[str, object]) -> bool:
    vul_pattern = record.get("Vul_Pattern")
    return vul_pattern == ["SLQ"]


def filter_jsonl(input_path: Path, output_path: Path) -> None:
    kept_count = 0
    dropped_count = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as src, output_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line_number, line in enumerate(src, start=1):
            record = json.loads(line)
            if "Vul_Pattern" not in record:
                raise ValueError(
                    f"Missing 'Vul_Pattern' field in input jsonl line {line_number}."
                )

            if should_drop(record):
                dropped_count += 1
                continue

            dst.write(json.dumps(record, ensure_ascii=False) + "\n")
            kept_count += 1

    print(
        f"Wrote {kept_count} records to {output_path} "
        f"after dropping {dropped_count} records."
    )


def main() -> None:
    args = parse_args()
    filter_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
