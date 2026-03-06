#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_TOOLS = [
    "ere",
    "redoshunter",
    "rengar",
    "rescue",
    "revealer",
]

TOOL_FILE_RE = re.compile(r"^1_detect_(?P<tool>.+)\.json$")


@dataclass
class Stats:
    total_lines: int = 0
    json_decode_errors: int = 0
    missing_file_or_line: int = 0
    verified_success_records: int = 0
    success_non_list_input: int = 0
    success_no_valid_attack: int = 0
    pattern_mismatch_warnings: int = 0


@dataclass
class GroundTruthEntry:
    engine: str
    file: str
    line: int
    pattern: str | None = None
    successful_tools: set[str] = field(default_factory=set)
    successful_attacks: list[dict[str, Any]] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "file": self.file,
            "line": self.line,
            "pattern": self.pattern,
            "successful_tools": sorted(self.successful_tools),
            "successful_attacks": self.successful_attacks,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract per-engine Ground Truth sets using Mode 4 verification logic."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("./expr/results"),
        help="Directory containing engine subdirs with 1_detect_*.json files.",
    )
    parser.add_argument(
        "--engines",
        nargs="*",
        default=None,
        help="Engine names to process. If omitted, auto-discover subdirectories.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("./expr/ground_truth"),
        help="Output directory for generated jsonl files.",
    )
    parser.add_argument(
        "--tools",
        nargs="*",
        default=DEFAULT_TOOLS,
        help="Allowed tool names. Defaults to draw_cactus.py tool list.",
    )
    parser.add_argument(
        "--strict-pattern-consistency",
        action="store_true",
        help="Fail fast if the same (file,line,engine) has conflicting pattern values.",
    )
    parser.add_argument(
        "--write-aggregate",
        action="store_true",
        help="Also write one merged file: ground_truth_all_engines.jsonl",
    )
    return parser.parse_args()


def is_verified_success(record: dict[str, Any]) -> bool:
    stderr = record.get("stderr", "")
    if isinstance(stderr, str) and "input is not a valid attack" in stderr:
        return False

    if record.get("timeout", False) is True:
        return True

    stdout = record.get("stdout", "")
    if not isinstance(stdout, str):
        return False

    return (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    )


def discover_engines(results_dir: Path) -> list[str]:
    if not results_dir.exists():
        return []
    return sorted([p.name for p in results_dir.iterdir() if p.is_dir()])


def discover_tool_files(engine_dir: Path, allowed_tools: set[str]) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for path in sorted(engine_dir.glob("1_detect_*.json")):
        m = TOOL_FILE_RE.match(path.name)
        if not m:
            continue
        tool = m.group("tool")
        if tool in allowed_tools:
            found.append((tool, path))
    return found


def extract_pattern_and_attacks(
    input_field: Any,
) -> tuple[str | None, list[dict[str, Any]]]:
    pattern: str | None = None
    attacks: list[dict[str, Any]] = []
    if not isinstance(input_field, list):
        return pattern, attacks

    for idx, attack in enumerate(input_field):
        if not isinstance(attack, dict):
            continue

        if pattern is None and isinstance(attack.get("pattern"), str):
            pattern = attack["pattern"]

        if (
            attack.get("is_redos") is True
            and isinstance(attack.get("prefix"), str)
            and isinstance(attack.get("infix"), str)
            and isinstance(attack.get("suffix"), str)
        ):
            attacks.append(
                {
                    "attack_index": idx,
                    "is_redos": True,
                    "prefix": attack["prefix"],
                    "infix": attack["infix"],
                    "suffix": attack["suffix"],
                    "repeat_times": attack.get("repeat_times"),
                }
            )
    return pattern, attacks


def process_engine(
    engine: str,
    engine_dir: Path,
    tools: set[str],
    strict_pattern_consistency: bool,
) -> tuple[list[dict[str, Any]], Stats]:
    stats = Stats()
    entries: dict[tuple[str, int], GroundTruthEntry] = {}

    for tool, file_path in discover_tool_files(engine_dir, tools):
        with file_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                stats.total_lines += 1
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    stats.json_decode_errors += 1
                    continue

                if not is_verified_success(rec):
                    continue
                stats.verified_success_records += 1

                src_file = rec.get("file")
                src_line = rec.get("line")
                if not isinstance(src_file, str) or not isinstance(src_line, int):
                    stats.missing_file_or_line += 1
                    continue

                key = (src_file, src_line)
                if key not in entries:
                    entries[key] = GroundTruthEntry(
                        engine=engine,
                        file=src_file,
                        line=src_line,
                    )
                entry = entries[key]
                entry.successful_tools.add(tool)

                pattern, attacks = extract_pattern_and_attacks(rec.get("input"))
                if not isinstance(rec.get("input"), list):
                    stats.success_non_list_input += 1

                if pattern is not None:
                    if entry.pattern is None:
                        entry.pattern = pattern
                    elif entry.pattern != pattern:
                        stats.pattern_mismatch_warnings += 1
                        message = (
                            f"[WARN] Pattern mismatch: engine={engine}, file={src_file}, "
                            f"line={src_line}, old={entry.pattern!r}, new={pattern!r}"
                        )
                        if strict_pattern_consistency:
                            raise ValueError(message)
                        print(message, file=sys.stderr)

                if not attacks:
                    stats.success_no_valid_attack += 1
                    continue

                for attack in attacks:
                    entry.successful_attacks.append({"tool": tool, **attack})

    out_records = [entries[k].to_record() for k in sorted(entries.keys())]
    return out_records, stats


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            # Keep JSONL safe for editors that treat U+2028/U+2029 as line separators.
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def print_engine_stats(engine: str, stats: Stats, count: int) -> None:
    print(
        (
            f"[{engine}] records={count}, lines={stats.total_lines}, "
            f"verified_success={stats.verified_success_records}, "
            f"json_errors={stats.json_decode_errors}, "
            f"missing_file_or_line={stats.missing_file_or_line}, "
            f"success_non_list_input={stats.success_non_list_input}, "
            f"success_no_valid_attack={stats.success_no_valid_attack}, "
            f"pattern_mismatch_warnings={stats.pattern_mismatch_warnings}"
        ),
        file=sys.stderr,
    )


def build_dedup_aggregate(
    all_records: list[dict[str, Any]], strict_pattern_consistency: bool
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, int], dict[str, Any]] = {}

    for rec in all_records:
        key = (rec["file"], rec["line"])
        engine = rec["engine"]
        pattern = rec.get("pattern")
        tools = rec.get("successful_tools", [])
        attacks = rec.get("successful_attacks", [])

        if key not in merged:
            merged[key] = {
                "file": rec["file"],
                "line": rec["line"],
                "pattern": pattern,
                "engines": set(),
                "engine_details": {},
            }

        dst = merged[key]
        if pattern is not None:
            if dst["pattern"] is None:
                dst["pattern"] = pattern
            elif dst["pattern"] != pattern:
                message = (
                    f"[WARN] Cross-engine pattern mismatch: file={rec['file']}, "
                    f"line={rec['line']}, old={dst['pattern']!r}, new={pattern!r}"
                )
                if strict_pattern_consistency:
                    raise ValueError(message)
                print(message, file=sys.stderr)

        dst["engines"].add(engine)
        dst["engine_details"][engine] = {
            "successful_tools": sorted(set(tools)),
            "successful_attacks": attacks,
        }

    out: list[dict[str, Any]] = []
    for key in sorted(merged.keys()):
        item = merged[key]
        out.append(
            {
                "file": item["file"],
                "line": item["line"],
                "pattern": item["pattern"],
                "engines": sorted(item["engines"]),
                "engine_details": {
                    e: item["engine_details"][e] for e in sorted(item["engine_details"])
                },
            }
        )
    return out


def main() -> int:
    args = parse_args()
    results_dir: Path = args.results_dir
    out_dir: Path = args.out_dir
    tools = set(args.tools)

    engines = args.engines if args.engines else discover_engines(results_dir)
    if not engines:
        print(f"No engines found in {results_dir}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[dict[str, Any]] = []
    for engine in engines:
        engine_dir = results_dir / engine
        if not engine_dir.is_dir():
            print(f"[WARN] Skip missing engine directory: {engine_dir}", file=sys.stderr)
            continue

        records, stats = process_engine(
            engine=engine,
            engine_dir=engine_dir,
            tools=tools,
            strict_pattern_consistency=args.strict_pattern_consistency,
        )
        output_file = out_dir / f"ground_truth_{engine}.jsonl"
        write_jsonl(output_file, records)
        print(f"[OK] Wrote {len(records)} records -> {output_file}", file=sys.stderr)
        print_engine_stats(engine, stats, len(records))
        all_records.extend(records)

    if args.write_aggregate:
        aggregate_path = out_dir / "ground_truth_all_engines.jsonl"
        dedup_records = build_dedup_aggregate(
            all_records, strict_pattern_consistency=args.strict_pattern_consistency
        )
        write_jsonl(aggregate_path, dedup_records)
        print(
            f"[OK] Wrote {len(dedup_records)} deduplicated records -> {aggregate_path}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
