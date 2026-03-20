#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError as exc:
    raise SystemExit(
        "openpyxl is required to read the xlsx file. Install it with: pip install openpyxl"
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge Source and Vul_Pattern from cve-cve414.xlsx into cve414.jsonl "
            "by matching the 'ReDoS-vulnerable Regex' column to the JSONL pattern field."
        )
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=Path("expr/data/cve-cve414.xlsx"),
        help="Path to the xlsx file.",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path("expr/data/cve414.jsonl"),
        help="Path to the source jsonl file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("expr/data/cve414_with_metadata.jsonl"),
        help="Path to the merged output jsonl file.",
    )
    return parser.parse_args()


def load_xlsx_rows(path: Path) -> list[dict[str, str]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    # Keep the same behavior as the previous XML-based implementation:
    # use the first worksheet in workbook order instead of the currently active tab.
    sheet = workbook.worksheets[0]
    rows = []
    for values in sheet.iter_rows(values_only=True):
        row = ["" if value is None else str(value) for value in values]
        rows.append(row)

    if not rows:
        raise ValueError(f"No rows found in xlsx file: {path}")
    workbook.close()
    return rows


def column_lookup(header_row: list[str]) -> dict[str, int]:
    return {name: index for index, name in enumerate(header_row)}


def parse_vul_pattern(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return raw.split()


def load_metadata_by_pattern(xlsx_path: Path) -> dict[str, deque[dict[str, object]]]:
    rows = load_xlsx_rows(xlsx_path)
    lookup = column_lookup(rows[0])
    required_columns = ["ReDoS-vulnerable Regex", "Source", "Vul_Pattern"]
    missing = [name for name in required_columns if name not in lookup]
    if missing:
        raise ValueError(f"Missing required columns in xlsx: {missing}")

    regex_column = lookup["ReDoS-vulnerable Regex"]
    source_column = lookup["Source"]
    vul_pattern_column = lookup["Vul_Pattern"]

    metadata_by_pattern: dict[str, deque[dict[str, object]]] = defaultdict(deque)
    for row in rows[1:]:
        pattern = row[regex_column] if regex_column < len(row) else ""
        if not pattern:
            continue
        metadata_by_pattern[pattern].append(
            {
                "Source": row[source_column] if source_column < len(row) else "",
                "Vul_Pattern": parse_vul_pattern(
                    row[vul_pattern_column] if vul_pattern_column < len(row) else ""
                ),
            }
        )
    return metadata_by_pattern


def merge_files(jsonl_path: Path, xlsx_path: Path, output_path: Path) -> None:
    metadata_by_pattern = load_metadata_by_pattern(xlsx_path)
    matched_count = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("r", encoding="utf-8") as src, output_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line_number, line in enumerate(src, start=1):
            record = json.loads(line)
            pattern = record.get("pattern")
            if pattern is None:
                raise ValueError(f"Missing 'pattern' field in jsonl line {line_number}.")
            if pattern not in metadata_by_pattern or not metadata_by_pattern[pattern]:
                raise ValueError(
                    f"No xlsx row left to match pattern from jsonl line {line_number}: {pattern!r}"
                )

            metadata = metadata_by_pattern[pattern].popleft()
            record["Vul_Pattern"] = metadata["Vul_Pattern"]
            record["Source"] = metadata["Source"]
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")
            matched_count += 1

    leftovers = {
        pattern: len(entries)
        for pattern, entries in metadata_by_pattern.items()
        if entries
    }
    if leftovers:
        sample_pattern, sample_count = next(iter(leftovers.items()))
        raise ValueError(
            "Not all xlsx rows were consumed. "
            f"Example leftover: {sample_pattern!r} has {sample_count} unmatched row(s)."
        )

    print(f"Merged {matched_count} records into {output_path}")


def main() -> None:
    args = parse_args()
    merge_files(args.jsonl, args.xlsx, args.output)


if __name__ == "__main__":
    main()
