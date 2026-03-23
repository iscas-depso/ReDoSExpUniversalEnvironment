#!/usr/bin/env python3
import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import re

TOOLS: List[str] = ["ere", "redoshunter", "regulator", "rengar", "revealer", "regexploit", "rescue"]
TOOL_DISPLAY = {
    "ere": "LARA",
    "redoshunter": "ReDoSHunter",
    "regulator": "Regulator",
    "rengar": "Rengar",
    "revealer": "Revealer",
    "regexploit": "Regexploit",
    "rescue": "ReScue",
}
ENGINES: List[str] = ["nodejs14", "python", "java11"]
# ENGINES: List[str] = ["nodejs14"]

ENGINE_DISPLAY = {"nodejs14": "Node.js", "python": "Python", "java11": "Java"}

DEFAULT_RESULTS_DIR = Path("expr/results")
DEFAULT_CVE_RESULTS_DIR = Path("expr/results-cve")

EXPECTED_COUNTS = {
    "nodejs14": 4415,
    "python": 4507,
    "java11": 5354,
    "union": 5847,
}

Key = Tuple[str, int]


PLOT_TITLE_FONTSIZE = 18
PLOT_LABEL_FONTSIZE = 15
PLOT_TICK_FONTSIZE = 13
PLOT_LEGEND_FONTSIZE = 13
PLOT_ANNOTATION_FONTSIZE = 12
PLOT_CACTUS_FIGSIZE = (9, 6)
PLOT_STACKBAR_FIGSIZE = (9, 6)
PLOT_UPSET_FIGSIZE = (11, 8)
PLOT_STACKBAR_TITLE_FONTSIZE = 16
PLOT_STACKBAR_LABEL_FONTSIZE = 13
PLOT_STACKBAR_TICK_FONTSIZE = 12
PLOT_STACKBAR_LEGEND_FONTSIZE = 12
PLOT_STACKBAR_ANNOTATION_FONTSIZE = 11
PLOT_STACKBAR_MIN_VISIBLE_PCT = 3


@dataclass
class DetectionRow:
    tool: str
    reported: int
    ref_coverage: int
    missed: int
    unconfirmed: int


@dataclass
class DetectionStackbarRow:
    tool: str
    other_tools_found: int
    only_other_tool: int
    both_found: int
    only_lara_found: int


@dataclass
class UniqueRow:
    tool: str
    unique_detections: int
    unique_attacks: int


@dataclass
class AttackStackbarRow:
    tool: str
    other_tools_found: int
    only_other_tool: int
    both_found: int
    only_lara_found: int


@dataclass
class DetectionUpSetRow:
    rank: int
    combination: str
    count: int


@dataclass
class PerformanceRow:
    tool: str
    median_time: float
    average_time: float
    median_memory: float
    average_memory: float
    timeouts: int
    ooms: int


@dataclass
class FnBreakdownRow:
    tool: str
    total: int
    timeout: int
    oom: int
    others: int


def iter_json_objects(path: Path) -> Iterator[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = text.strip()
    if not text:
        return

    # 兼容 JSON 数组
    if text.startswith("["):
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        return

    # 兼容 JSONL / 连续 JSON 对象
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break
        try:
            obj, next_idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            # 跳到下一行继续尝试，尽量鲁棒
            nl = text.find("\n", idx)
            if nl == -1:
                break
            idx = nl + 1
            continue
        if isinstance(obj, dict):
            yield obj
        idx = next_idx


def parse_key(record: dict) -> Key:
    return (str(record.get("file")), int(record.get("line", -1)))


def export_sort_key(item: Key) -> Tuple[str, int, str]:
    return (Path(item[0]).name, item[1], item[0])


def discover_tools(results_dir: Path, prefix: str = "1_expr") -> List[str]:
    available: Set[str] = set()
    marker = f"{prefix}_"
    for path in sorted(results_dir.glob(f"{prefix}_*.json*")):
        name = path.name
        if not name.startswith(marker):
            continue
        suffix = name[len(marker):]
        json_idx = suffix.find(".json")
        if json_idx != -1:
            suffix = suffix[:json_idx]
        if suffix:
            available.add(suffix)

    return [tool for tool in TOOLS if tool in available]


def claims_redos(record: dict) -> bool:
    output_field = record.get("output")
    if not output_field:
        return False
    try:
        parsed = json.loads(output_field)
    except Exception:
        return False
    if not isinstance(parsed, list):
        return False
    for item in parsed:
        if isinstance(item, dict) and item.get("is_redos") is True:
            return True
    return False


def verification_success(record: dict) -> bool:
    stderr = str(record.get("stderr", ""))
    if "input is not a valid attack" in stderr:
        return False

    if record.get("timeout", False) is True:
        return True

    stdout = str(record.get("stdout", ""))
    return (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    )


def parse_cputime(stdout_str: str) -> float | None:
    if not stdout_str:
        return None
    match = re.search(r"cputime=([\d\.]+)s", stdout_str)
    return float(match.group(1)) if match else None


def parse_memory(stdout_str: str) -> float | None:
    if not stdout_str:
        return None
    match = re.search(r"memory=(\d+)B", stdout_str)
    return int(match.group(1)) / (1024 * 1024) if match else None


def get_termination_reason(record: dict) -> str:
    stdout = str(record.get("stdout", ""))
    if "terminationreason=memory" in stdout:
        return "memory"
    if record.get("timeout", False) is True:
        return "timeout"
    if (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    ):
        return "timeout"
    return ""


def is_timeout_record(record: dict) -> bool:
    return get_termination_reason(record) == "timeout"


def is_oom_record(record: dict) -> bool:
    return get_termination_reason(record) == "memory"


def find_file(root: Path, prefix: str, tool: str) -> Path:
    direct = root / f"{prefix}_{tool}.json"
    if direct.exists():
        return direct

    # 兼容 .jsonl 或其他后缀
    candidates = sorted(root.glob(f"{prefix}_{tool}.json*"))
    if not candidates:
        raise FileNotFoundError(f"Missing file for tool={tool}: {root / (prefix + '_' + tool + '.json*')}")
    return candidates[0]


def load_reported_sets_for_tools(results_dir: Path, tools: Iterable[str]) -> Dict[str, Set[Key]]:
    reported: Dict[str, Set[Key]] = {t: set() for t in tools}
    for tool in tools:
        path = find_file(results_dir, "1_expr", tool)
        for rec in iter_json_objects(path):
            if claims_redos(rec):
                reported[tool].add(parse_key(rec))
    return reported


def load_reported_sets(results_dir: Path) -> Dict[str, Set[Key]]:
    return load_reported_sets_for_tools(results_dir, TOOLS)


def load_records_by_key(root: Path, prefix: str, tool: str) -> Dict[Key, dict]:
    path = find_file(root, prefix, tool)
    records: Dict[Key, dict] = {}
    for rec in iter_json_objects(path):
        records[parse_key(rec)] = rec
    return records


def load_reference_records(
    results_dir: Path,
    tools: Iterable[str],
    prefix: str = "1_expr",
) -> Dict[Key, dict]:
    records: Dict[Key, dict] = {}
    for tool in tools:
        path = find_file(results_dir, prefix, tool)
        for rec in iter_json_objects(path):
            key = parse_key(rec)
            records.setdefault(key, rec)
    return records


def is_cve_results_dir(results_dir: Path) -> bool:
    return results_dir.name == DEFAULT_CVE_RESULTS_DIR.name


def build_performance_rows(results_dir: Path) -> List[PerformanceRow]:
    rows: List[PerformanceRow] = []
    for tool in TOOLS:
        path = find_file(results_dir, "1_expr", tool)
        times: List[float] = []
        memories: List[float] = []
        timeouts = 0
        ooms = 0
        for rec in iter_json_objects(path):
            timed_out = is_timeout_record(rec)
            oom = is_oom_record(rec)
            if timed_out:
                timeouts += 1
            if oom:
                ooms += 1
            cputime = parse_cputime(str(rec.get("stdout", "")))
            if cputime is not None and not timed_out and not oom:
                times.append(cputime)
            memory = parse_memory(str(rec.get("stdout", "")))
            if memory is not None and not timed_out and not oom:
                memories.append(memory)

        if times:
            median_time = float(np.median(times))
            average_time = float(np.mean(times))
        else:
            median_time = 0.0
            average_time = 0.0
        if memories:
            median_memory = float(np.median(memories))
            average_memory = float(np.mean(memories))
        else:
            median_memory = 0.0
            average_memory = 0.0

        rows.append(
            PerformanceRow(
                tool=tool,
                median_time=median_time,
                average_time=average_time,
                median_memory=median_memory,
                average_memory=average_memory,
                timeouts=timeouts,
                ooms=ooms,
            )
        )
    return rows


def load_attack_sets_per_engine(results_dir: Path, engine: str) -> Dict[str, Set[Key]]:
    engine_dir = results_dir / engine
    attacks: Dict[str, Set[Key]] = {t: set() for t in TOOLS}
    for tool in TOOLS:
        path = find_file(engine_dir, "1_detect", tool)
        for rec in iter_json_objects(path):
            if verification_success(rec):
                attacks[tool].add(parse_key(rec))
    return attacks


def format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def print_detection_table(rows: List[DetectionRow]) -> None:
    print("\\n=== Table: Detection (tab:detection) ===")
    print(f"{'Tool':<12} {'Reported':>10} {'Reference Coverage':>20} {'Missed':>10} {'Unconfirmed':>14}")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<12} {r.reported:>10} {r.ref_coverage:>20} {r.missed:>10} {r.unconfirmed:>14}"
        )


def print_detection_latex(rows: List[DetectionRow]) -> None:
    print("\\nLaTeX rows for tab:detection:")
    for r in rows:
        line = (
            f"{TOOL_DISPLAY[r.tool]} & {r.reported} & {r.ref_coverage}"
            f" & {r.missed} & {r.unconfirmed} \\\\" 
        )
        print(line)


def build_confirmed_detection_rows(
    reported_sets: Dict[str, Set[Key]],
    confirmed_keys: Set[Key],
    tools: Iterable[str],
) -> List[DetectionRow]:
    rows: List[DetectionRow] = []
    for tool in tools:
        hit = len(reported_sets[tool] & confirmed_keys)
        rows.append(
            DetectionRow(
                tool=tool,
                reported=hit,
                ref_coverage=hit,
                missed=len(confirmed_keys) - hit,
                unconfirmed=0,
            )
        )
    return rows


def print_confirmed_detection_table(rows: List[DetectionRow], confirmed_total: int) -> None:
    print("\n=== Table: Confirmed CVE Detection (tab:cve-detection) ===")
    print(f"Confirmed instances: {confirmed_total}")
    print(f"{'Tool':<14} {'Detected':>10} {'Recall':>10} {'Missed':>10}")
    for r in rows:
        recall = (r.ref_coverage / confirmed_total) if confirmed_total else 0.0
        print(
            f"{TOOL_DISPLAY.get(r.tool, r.tool):<14} {r.ref_coverage:>10} {format_pct(recall):>10} {r.missed:>10}"
        )


def write_confirmed_detection_summary_csv(
    rows: List[DetectionRow],
    confirmed_total: int,
    output_csv: Path,
) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tool", "display_name", "detected", "missed", "recall"],
        )
        writer.writeheader()
        for r in rows:
            recall = (r.ref_coverage / confirmed_total) if confirmed_total else 0.0
            writer.writerow(
                {
                    "tool": r.tool,
                    "display_name": TOOL_DISPLAY.get(r.tool, r.tool),
                    "detected": r.ref_coverage,
                    "missed": r.missed,
                    "recall": f"{recall:.6f}",
                }
            )


def write_confirmed_detection_matrix_csv(
    reported_sets: Dict[str, Set[Key]],
    reference_records: Dict[Key, dict],
    tools: Iterable[str],
    output_csv: Path,
) -> None:
    tool_list = list(tools)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "file",
            "line",
            "input",
            *tool_list,
            "detected_by_count",
            "detected_by_tools",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        def sort_key(item: Key) -> Tuple[str, int, str]:
            return (Path(item[0]).name, item[1], item[0])

        for key in sorted(reference_records, key=sort_key):
            rec = reference_records[key]
            flags = {tool: int(key in reported_sets[tool]) for tool in tool_list}
            detected_tools = [
                TOOL_DISPLAY.get(tool, tool) for tool in tool_list if flags[tool]
            ]
            writer.writerow(
                {
                    "file": key[0],
                    "line": key[1],
                    "input": rec.get("input", ""),
                    **flags,
                    "detected_by_count": sum(flags.values()),
                    "detected_by_tools": "; ".join(detected_tools),
                }
            )


def run_confirmed_only_mode(results_dir: Path) -> None:
    tools = discover_tools(results_dir, prefix="1_expr")
    if not tools:
        raise FileNotFoundError(f"No 1_expr_<tool>.json files found under {results_dir}")

    reference_records = load_reference_records(results_dir, tools, prefix="1_expr")
    confirmed_keys = set(reference_records)
    reported_sets = load_reported_sets_for_tools(results_dir, tools)
    detection_rows = build_confirmed_detection_rows(reported_sets, confirmed_keys, tools)
    lara_fn_breakdown_row = build_lara_fn_breakdown_row(
        results_dir, reported_sets, confirmed_keys
    )
    detection_stackbar_rows = build_detection_stackbar_rows(
        reported_sets, confirmed_keys, our_tool="ere"
    )
    detection_upset_rows, detection_upset_uncovered = build_detection_upset_table_rows(
        reported_sets, confirmed_keys
    )

    print_confirmed_detection_table(detection_rows, len(confirmed_keys))
    print_confirmed_detection_stackbar_table(detection_stackbar_rows)
    print_detection_upset_table(detection_upset_rows, detection_upset_uncovered)
    print_confirmed_lara_fn_breakdown_table(lara_fn_breakdown_row)

    output_dir = results_dir.parent / "plots-cve"
    summary_csv = output_dir / "cve_detection_summary.csv"
    matrix_csv = output_dir / "cve_detection_matrix.csv"
    stackbar_pdf = output_dir / "cve_detection_stackbar.pdf"
    upset_pdf = output_dir / "cve_detection_upset.pdf"
    lara_fn_csv = output_dir / "cve_lara_fn.csv"
    write_confirmed_detection_summary_csv(detection_rows, len(confirmed_keys), summary_csv)
    write_confirmed_detection_matrix_csv(reported_sets, reference_records, tools, matrix_csv)
    plot_detection_stackbar(reported_sets, confirmed_keys, stackbar_pdf, our_tool="ere")
    plot_detection_upset(reported_sets, confirmed_keys, upset_pdf)
    write_confirmed_lara_fn_csv(
        results_dir,
        reported_sets,
        reference_records,
        tools,
        lara_fn_csv,
    )

    print(f"Saved CVE detection summary CSV: {summary_csv}")
    print(f"Saved CVE detection matrix CSV: {matrix_csv}")
    print(f"Saved CVE detection stackbar PDF: {stackbar_pdf}")
    print(f"Saved CVE detection upset PDF: {upset_pdf}")
    print(f"Saved CVE LARA FN CSV: {lara_fn_csv}")


def run_standard_mode(results_dir: Path) -> None:
    missing_engines = [eng for eng in ENGINES if not (results_dir / eng).exists()]
    if missing_engines:
        raise FileNotFoundError(
            f"{results_dir} is missing engine result dirs: {', '.join(missing_engines)}. "
            f"For confirmed CVE statistics, use {DEFAULT_CVE_RESULTS_DIR}."
        )

    # R_T: each tool's reported vulnerable set
    reported_sets = load_reported_sets(results_dir)
    performance_rows = build_performance_rows(results_dir)

    # A_T(engine): each tool's successful attack set on each engine
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]] = {}
    for eng in ENGINES:
        attacks_by_engine[eng] = load_attack_sets_per_engine(results_dir, eng)
    attack_union_sets = build_attack_union_sets(attacks_by_engine)

    # V_engine and global V (union over engines)
    v_engine: Dict[str, Set[Key]] = {}
    for eng in ENGINES:
        v_engine[eng] = set().union(*attacks_by_engine[eng].values())
    v_union = set().union(*v_engine.values())
    attack_time_cactus, attack_memory_cactus = build_attack_union_cactus_data(
        results_dir, attack_union_sets
    )
    marked_time_cactus, marked_memory_cactus = build_marked_union_cactus_data(
        results_dir, v_union
    )

    # Detection table metrics against global V
    detection_rows: List[DetectionRow] = []
    for tool in TOOLS:
        r_set = reported_sets[tool]
        hit = len(r_set & v_union)
        reported = len(r_set)
        missed = len(v_union - r_set)
        unconfirmed = len(r_set - v_union)
        detection_rows.append(
            DetectionRow(
                tool=tool,
                reported=reported,
                ref_coverage=hit,
                missed=missed,
                unconfirmed=unconfirmed,
            )
        )

    # Print outputs
    print_detection_table(detection_rows)
    print_detection_latex(detection_rows)
    print_attack_all(attacks_by_engine, v_union)
    # print_verify_counts(v_engine, v_union)
    print_detection_stackbar_table(
        build_detection_stackbar_rows(reported_sets, v_union, our_tool="ere")
    )
    detection_upset_rows, detection_upset_uncovered = build_detection_upset_table_rows(
        reported_sets, v_union
    )
    print_detection_upset_table(
        detection_upset_rows, detection_upset_uncovered
    )
    unique_rows = build_unique_rows(reported_sets, attacks_by_engine, v_union)
    print_unique_table(unique_rows)
    print_unique_latex(unique_rows)
    attack_stackbar_rows, attack_universe = build_attack_stackbar_rows(
        attacks_by_engine, our_tool="ere"
    )
    print_attack_stackbar_table(attack_stackbar_rows, len(attack_universe))
    print_without_lara_stats(attacks_by_engine, v_union)
    print_performance_table(performance_rows)
    print_performance_latex(performance_rows)
    lara_fn_breakdown_row = build_lara_fn_breakdown_row(results_dir, reported_sets, v_union)
    print_lara_fn_breakdown_table(lara_fn_breakdown_row)
    print_lara_fn_breakdown_latex(lara_fn_breakdown_row)
    lara_fn_csv = results_dir.parent / "plots" / "lara_fn.csv"
    unique_detection_csv = results_dir.parent / "plots" / "unique_detections.csv"
    unique_attack_csv = results_dir.parent / "plots" / "unique_attacks.csv"
    write_lara_fn_csv(results_dir, reported_sets, attacks_by_engine, v_union, lara_fn_csv)
    write_unique_detection_csv(
        results_dir, reported_sets, attacks_by_engine, v_union, unique_detection_csv
    )
    write_unique_attack_csv(
        results_dir, reported_sets, attacks_by_engine, v_union, unique_attack_csv
    )
    print(f"Saved LARA FN CSV: {lara_fn_csv}")
    print(f"Saved unique detections CSV: {unique_detection_csv}")
    print(f"Saved unique attacks CSV: {unique_attack_csv}")

    detection_fig = results_dir.parent / "plots" / "detection_stackbar.pdf"
    plot_detection_stackbar(reported_sets, v_union, detection_fig, our_tool="ere")
    print(f"\nSaved detection stackbar PDF: {detection_fig}")
    detection_upset_fig = results_dir.parent / "plots" / "detection_upset.pdf"
    plot_detection_upset(reported_sets, v_union, detection_upset_fig)
    print(f"Saved detection upset PDF: {detection_upset_fig}")
    attack_fig = results_dir.parent / "plots" / "unique_attack_stackbar.pdf"
    plot_attack_stackbar(attacks_by_engine, attack_fig, our_tool="ere")
    print(f"Saved attack stackbar PDF: {attack_fig}")
    attack_time_cactus_fig = results_dir.parent / "plots" / "attack_union_cactus_time.pdf"
    plot_cactus(
        attack_time_cactus,
        attack_time_cactus_fig,
        limit_value=600.0,
        metric="time",
        mode_desc="At Least One Engine Attack Success",
    )
    print(f"Saved attack-union time cactus PDF: {attack_time_cactus_fig}")
    attack_memory_cactus_fig = results_dir.parent / "plots" / "attack_union_cactus_memory.pdf"
    plot_cactus(
        attack_memory_cactus,
        attack_memory_cactus_fig,
        limit_value=10240.0,
        metric="memory",
        mode_desc="At Least One Engine Attack Success",
    )
    print(f"Saved attack-union memory cactus PDF: {attack_memory_cactus_fig}")
    marked_time_cactus_fig = results_dir.parent / "plots" / "marked_union_cactus_time.pdf"
    plot_cactus(
        marked_time_cactus,
        marked_time_cactus_fig,
        limit_value=600.0,
        metric="time",
        mode_desc="Confirmed Vulnerability Set V",
    )
    print(f"Saved marked-union time cactus PDF: {marked_time_cactus_fig}")
    marked_memory_cactus_fig = results_dir.parent / "plots" / "marked_union_cactus_memory.pdf"
    plot_cactus(
        marked_memory_cactus,
        marked_memory_cactus_fig,
        limit_value=10240.0,
        metric="memory",
        mode_desc="Confirmed Vulnerability Set V",
    )
    print(f"Saved marked-union memory cactus PDF: {marked_memory_cactus_fig}")


def union_attacks_for_tool(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    tool: str,
) -> Set[Key]:
    return set().union(*(attacks_by_engine[eng][tool] for eng in ENGINES))


def print_attack_all(attacks_by_engine: Dict[str, Dict[str, Set[Key]]], v_union: Set[Key]) -> None:
    print("\\n=== Attack Success Count by Engine (for tab:attack-all) ===")
    engine_headers = [ENGINE_DISPLAY.get(eng, eng) for eng in ENGINES]
    header = (
        f"{'Tool':<12}"
        + "".join(f" {name:>8}" for name in engine_headers)
        + f" {'At least one':>13} {'Attack Recall':>14}"
    )
    print(header)
    for tool in TOOLS:
        counts_by_engine = [len(attacks_by_engine[eng][tool]) for eng in ENGINES]
        union_n = len(union_attacks_for_tool(attacks_by_engine, tool))
        recall = (union_n / len(v_union)) if v_union else 0.0
        print(
            f"{TOOL_DISPLAY[tool]:<12}"
            + "".join(f" {count:>8}" for count in counts_by_engine)
            + f" {union_n:>13} {format_pct(recall):>14}"
        )

    print("-" * len(header))
    print(
        f"{'Marked total':<12}"
        + "".join(
            f" {len(set().union(*attacks_by_engine[eng].values())):>8}"
            for eng in ENGINES
        )
        + f" {len(v_union):>13}"
        + f" {'--':>14}"
    )


def print_verify_counts(v_engine: Dict[str, Set[Key]], v_union: Set[Key]) -> None:
    print("\\n=== Verify Marked Counts (paper numbers) ===")
    actual = {
        **{eng: len(v_engine[eng]) for eng in ENGINES},
        "union": len(v_union),
    }

    for k in [*ENGINES, "union"]:
        name = ENGINE_DISPLAY.get(k, k)
        exp = EXPECTED_COUNTS[k]
        got = actual[k]
        status = "OK" if got == exp else "MISMATCH"
        print(f"{name:<8}: expected={exp}, got={got} -> {status}")


def build_detection_stackbar_rows(
    reported_sets: Dict[str, Set[Key]],
    v_union: Set[Key],
    our_tool: str = "ere",
) -> List[DetectionStackbarRow]:
    if our_tool not in reported_sets:
        raise ValueError(f"our_tool={our_tool} not in reported sets")
    if not v_union:
        raise ValueError("Global verified set V is empty, cannot build detection stackbar rows.")

    det_sets: Dict[str, Set[Key]] = {t: (reported_sets[t] & v_union) for t in TOOLS}
    our_set = det_sets[our_tool]
    rows: List[DetectionStackbarRow] = []

    for t in TOOLS:
        if t == our_tool:
            continue
        other_set = det_sets[t]
        rows.append(
            DetectionStackbarRow(
                tool=t,
                other_tools_found=len(v_union - (our_set | other_set)),
                only_other_tool=len(other_set - our_set),
                both_found=len(our_set & other_set),
                only_lara_found=len(our_set - other_set),
            )
        )

    return rows


def print_detection_stackbar_table(rows: List[DetectionStackbarRow]) -> None:
    print("\n=== Detection Stackbar Data (for detection_stackbar.pdf) ===")
    print(
        f"{'Compare To':<14} {'Other Tools Found':>18} {'Only Other Tool':>17} {'Both Found':>12} {'Only LARA Found':>17}"
    )
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<14} {r.other_tools_found:>18} {r.only_other_tool:>17} {r.both_found:>12} {r.only_lara_found:>17}"
        )


def print_confirmed_detection_stackbar_table(rows: List[DetectionStackbarRow]) -> None:
    print("\n=== Confirmed CVE Detection Stackbar Data (for cve_detection_stackbar.pdf) ===")
    print(
        f"{'Compare To':<14} {'Other Tools Found':>18} {'Only Other Tool':>17} {'Both Found':>12} {'Only LARA Found':>17}"
    )
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<14} {r.other_tools_found:>18} {r.only_other_tool:>17} {r.both_found:>12} {r.only_lara_found:>17}"
        )


def build_detection_upset_table_rows(
    reported_sets: Dict[str, Set[Key]],
    v_union: Set[Key],
    top_k: Optional[int] = None,
) -> Tuple[List[DetectionUpSetRow], int]:
    if not v_union:
        raise ValueError("Global verified set V is empty, cannot build detection upset rows.")

    det_sets: Dict[str, Set[Key]] = {t: (reported_sets[t] & v_union) for t in TOOLS}
    combo_counts: Dict[Tuple[bool, ...], int] = {}
    uncovered = 0

    for key in v_union:
        combo = tuple(key in det_sets[t] for t in TOOLS)
        if any(combo):
            combo_counts[combo] = combo_counts.get(combo, 0) + 1
        else:
            uncovered += 1

    combos = sorted(
        combo_counts.items(),
        key=lambda item: (-item[1], -sum(item[0]), item[0]),
    )
    if top_k is not None:
        combos = combos[:top_k]

    rows: List[DetectionUpSetRow] = []
    for idx, (combo, cnt) in enumerate(combos, start=1):
        names = [TOOL_DISPLAY[t] for t, present in zip(TOOLS, combo) if present]
        rows.append(
            DetectionUpSetRow(
                rank=idx,
                combination=" + ".join(names),
                count=cnt,
            )
        )
    return rows, uncovered


def print_detection_upset_table(
    rows: List[DetectionUpSetRow],
    uncovered: int,
    top_k: Optional[int] = None,
) -> None:
    scope = "all intersections" if top_k is None else f"top {top_k}"
    print(f"\n=== Detection UpSet Data (for detection_upset.pdf, {scope}) ===")
    print(f"{'Rank':<6} {'Tool Combination':<72} {'Count':>8}")
    for r in rows:
        print(f"{r.rank:<6} {r.combination:<72} {r.count:>8}")
    print(f"{'Not detected by any tool in V':<78} {uncovered:>8}")


def build_unique_rows(
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
) -> List[UniqueRow]:
    unique_detection_sets, unique_attack_sets = build_unique_sets(
        reported_sets, attacks_by_engine, v_union
    )

    rows: List[UniqueRow] = []
    for tool in TOOLS:
        rows.append(
            UniqueRow(
                tool=tool,
                unique_detections=len(unique_detection_sets[tool]),
                unique_attacks=len(unique_attack_sets[tool]),
            )
        )
    return rows


def build_unique_sets(
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
) -> Tuple[Dict[str, Set[Key]], Dict[str, Set[Key]]]:
    detection_hits: Dict[str, Set[Key]] = {t: (reported_sets[t] & v_union) for t in TOOLS}
    attack_union_sets: Dict[str, Set[Key]] = {
        t: union_attacks_for_tool(attacks_by_engine, t)
        for t in TOOLS
    }

    unique_detection_sets: Dict[str, Set[Key]] = {}
    unique_attack_sets: Dict[str, Set[Key]] = {}
    for tool in TOOLS:
        other_detection_union = set().union(
            *[detection_hits[t] for t in TOOLS if t != tool]
        )
        other_attack_union = set().union(
            *[attack_union_sets[t] for t in TOOLS if t != tool]
        )
        unique_detection_sets[tool] = detection_hits[tool] - other_detection_union
        unique_attack_sets[tool] = attack_union_sets[tool] - other_attack_union

    return unique_detection_sets, unique_attack_sets


def print_unique_table(rows: List[UniqueRow]) -> None:
    print("\n=== Unique Contribution Table (for tab:unique) ===")
    print(f"{'Tool':<12} {'Unique Detections':>18} {'Unique Attacks':>16}")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<12} {r.unique_detections:>18} {r.unique_attacks:>16}"
        )


def print_unique_latex(rows: List[UniqueRow]) -> None:
    print("\nLaTeX rows for tab:unique:")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]} & {r.unique_detections} & {r.unique_attacks} \\\\"
        )


def build_attack_stackbar_rows(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    our_tool: str = "ere",
) -> Tuple[List[AttackStackbarRow], Set[Key]]:
    attack_union_sets: Dict[str, Set[Key]] = {
        t: union_attacks_for_tool(attacks_by_engine, t)
        for t in TOOLS
    }
    v_attack_union = set().union(*attack_union_sets.values())
    our_set = attack_union_sets[our_tool]

    rows: List[AttackStackbarRow] = []
    for t in TOOLS:
        if t == our_tool:
            continue
        other_set = attack_union_sets[t]
        rows.append(
            AttackStackbarRow(
                tool=t,
                other_tools_found=len(v_attack_union - (our_set | other_set)),
                only_other_tool=len(other_set - our_set),
                both_found=len(our_set & other_set),
                only_lara_found=len(our_set - other_set),
            )
        )
    return rows, v_attack_union


def print_attack_stackbar_table(rows: List[AttackStackbarRow], attack_universe_size: int) -> None:
    print("\n=== Attack Stackbar Data (for unique_attack_stackbar.pdf) ===")
    print(f"Attack universe size: {attack_universe_size}")
    print(
        f"{'Compare To':<14} {'Other Tools Found':>18} {'Only Other Tool':>17} {'Both Found':>12} {'Only LARA Found':>17}"
    )
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<14} {r.other_tools_found:>18} {r.only_other_tool:>17} {r.both_found:>12} {r.only_lara_found:>17}"
        )


def build_attack_union_sets(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
) -> Dict[str, Set[Key]]:
    return {
        t: union_attacks_for_tool(attacks_by_engine, t)
        for t in TOOLS
    }


def build_attack_union_cactus_data(
    results_dir: Path,
    attack_union_sets: Dict[str, Set[Key]],
) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
    time_data: Dict[str, List[float]] = {t: [] for t in TOOLS}
    memory_data: Dict[str, List[float]] = {t: [] for t in TOOLS}

    for tool in TOOLS:
        path = find_file(results_dir, "1_expr", tool)
        valid_keys = attack_union_sets[tool]
        for rec in iter_json_objects(path):
            key = parse_key(rec)
            if key not in valid_keys:
                continue
            if not claims_redos(rec):
                continue
            if is_timeout_record(rec) or is_oom_record(rec):
                continue

            cputime = parse_cputime(str(rec.get("stdout", "")))
            memory = parse_memory(str(rec.get("stdout", "")))
            if cputime is not None:
                time_data[tool].append(cputime)
            if memory is not None:
                memory_data[tool].append(memory)

    for tool in TOOLS:
        time_data[tool].sort()
        memory_data[tool].sort()

    return time_data, memory_data


def build_marked_union_cactus_data(
    results_dir: Path,
    v_union: Set[Key],
) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
    time_data: Dict[str, List[float]] = {t: [] for t in TOOLS}
    memory_data: Dict[str, List[float]] = {t: [] for t in TOOLS}

    for tool in TOOLS:
        path = find_file(results_dir, "1_expr", tool)
        for rec in iter_json_objects(path):
            key = parse_key(rec)
            if key not in v_union:
                continue
            if not claims_redos(rec):
                continue
            if is_timeout_record(rec) or is_oom_record(rec):
                continue

            cputime = parse_cputime(str(rec.get("stdout", "")))
            memory = parse_memory(str(rec.get("stdout", "")))
            if cputime is not None:
                time_data[tool].append(cputime)
            if memory is not None:
                memory_data[tool].append(memory)

    for tool in TOOLS:
        time_data[tool].sort()
        memory_data[tool].sort()

    return time_data, memory_data


def plot_cactus(
    data_dict: Dict[str, List[float]],
    output_image: Path,
    limit_value: float,
    metric: str,
    mode_desc: str,
) -> None:
    fig, ax = plt.subplots(figsize=PLOT_CACTUS_FIGSIZE)
    colors = plt.get_cmap("tab10").colors
    linestyles = ["-", "--", "-.", ":"]
    max_solved = 0

    if metric == "time":
        y_label = "CPU Time (s)"
        title = "Cactus Plot of CPU Time"
        min_val = 0.01
    else:
        y_label = "Memory Usage (MB)"
        title = "Cactus Plot of Memory Usage"
        min_val = 1.0

    for idx, tool in enumerate(TOOLS):
        vals = data_dict.get(tool, [])
        if not vals:
            continue
        valid_vals = [v for v in vals if v < limit_value]
        if not valid_vals:
            continue
        max_solved = max(max_solved, len(valid_vals))
        ax.plot(
            range(1, len(valid_vals) + 1),
            valid_vals,
            label=f"{TOOL_DISPLAY[tool]} ({len(valid_vals)})",
            color=colors[idx % len(colors)],
            linestyle=linestyles[idx % len(linestyles)],
            linewidth=2,
            alpha=0.8,
        )

    ax.set_xlabel("Number of Solved Instances", fontsize=PLOT_LABEL_FONTSIZE)
    ax.set_ylabel(f"{y_label} - Log Scale", fontsize=PLOT_LABEL_FONTSIZE)
    ax.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)
    ax.set_yscale("log")
    ax.set_ylim(bottom=min_val, top=limit_value * 1.5)
    ax.set_xlim(left=0, right=max_solved * 1.05 if max_solved > 0 else 10)
    ax.axhline(
        y=limit_value,
        color="r",
        linestyle="--",
        alpha=0.5,
    )
    ax.text(
        0.98,
        limit_value,
        f"Limit = {int(limit_value)}",
        color="r",
        fontsize=PLOT_ANNOTATION_FONTSIZE,
        ha="right",
        va="bottom",
        transform=ax.get_yaxis_transform(),
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.5},
    )
    ax.grid(True, which="major", ls="-", alpha=0.4)
    ax.grid(True, which="minor", ls=":", alpha=0.2)
    ax.legend(loc="lower right", fontsize=PLOT_LEGEND_FONTSIZE)

    output_image.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close(fig)


def plot_attack_stackbar(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    output_pdf: Path,
    our_tool: str = "ere",
) -> None:
    rows, _ = build_attack_stackbar_rows(attacks_by_engine, our_tool=our_tool)
    if not rows:
        raise ValueError("No baseline tools to compare against.")

    labels = [TOOL_DISPLAY[r.tool] for r in rows]
    counts = np.array(
        [
            [r.other_tools_found for r in rows],
            [r.only_other_tool for r in rows],
            [r.both_found for r in rows],
            [r.only_lara_found for r in rows],
        ],
        dtype=float,
    )
    totals = counts.sum(axis=0)
    totals[totals == 0] = 1.0

    pct = counts / totals * 100.0
    min_vis_pct = PLOT_STACKBAR_MIN_VISIBLE_PCT
    vis_pct = pct.copy()
    vis_pct[(vis_pct > 0) & (vis_pct < min_vis_pct)] = min_vis_pct
    vis_totals = vis_pct.sum(axis=0)
    vis_totals[vis_totals == 0] = 1.0
    vis_pct = vis_pct / vis_totals * 100.0

    colors = ["#eeeeee", "#f8cecc", "#fff2cc", "#dae8fc"]
    legend_labels = [
        "Other Tools Found",
        "Only Other Tool",
        "Both Found",
        "Only LARA Found",
    ]

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=PLOT_STACKBAR_FIGSIZE)
    x = np.arange(len(labels))
    bottom = np.zeros(len(labels), dtype=float)
    bars = []

    for i in range(4):
        bar = ax.bar(
            x,
            vis_pct[i],
            bottom=bottom,
            color=colors[i],
            edgecolor="#444444",
            linewidth=0.5,
            width=0.7,
            label=legend_labels[i],
        )
        bars.append(bar)
        bottom += vis_pct[i]

    for i, bar_group in enumerate(bars):
        labels_count = [f"{int(v)}" if v > 0 else "" for v in counts[i]]
        ax.bar_label(
            bar_group,
            labels=labels_count,
            label_type="center",
            fontsize=PLOT_STACKBAR_ANNOTATION_FONTSIZE,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, fontsize=PLOT_STACKBAR_TICK_FONTSIZE)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage over Attack Success Union (%)", fontsize=PLOT_STACKBAR_LABEL_FONTSIZE)
    ax.set_xlabel("Pairwise Comparison with LARA", fontsize=PLOT_STACKBAR_LABEL_FONTSIZE)
    ax.tick_params(axis="y", labelsize=PLOT_STACKBAR_TICK_FONTSIZE)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=2,
        frameon=False,
        fontsize=PLOT_STACKBAR_LEGEND_FONTSIZE,
        columnspacing=1.2,
        handletextpad=0.6,
        labelspacing=0.35,
    )

    # fig.subplots_adjust(left=0.15, right=0.94, bottom=0.14, top=0.8)
    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close(fig)


def print_without_lara_stats(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
) -> None:
    baseline_union = set().union(
        *[
            union_attacks_for_tool(attacks_by_engine, t)
            for t in TOOLS
            if t != "ere"
        ]
    )
    lost = len(v_union - baseline_union)
    pct = (lost / len(v_union) * 100.0) if v_union else 0.0
    print("\n=== Without LARA Marked-Set Loss ===")
    print(f"Lost confirmed vulnerabilities without LARA: {lost}")
    print(f"Loss ratio over V: {pct:.2f}%")


def print_performance_table(rows: List[PerformanceRow]) -> None:
    print("\n=== Performance Table (for tab:performance) ===")
    print(
        f"{'Tool':<12} {'Median Time (s)':>18} {'Average Time (s)':>18} {'Median Mem (MB)':>18} {'Average Mem (MB)':>18} {'Timeout/OOM':>14}"
    )
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<12} {r.median_time:>18.4f} {r.average_time:>18.4f} {r.median_memory:>18.2f} {r.average_memory:>18.2f} {f'{r.timeouts}/{r.ooms}':>14}"
        )


def print_performance_latex(rows: List[PerformanceRow]) -> None:
    print("\nLaTeX rows for tab:performance:")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]} & {r.median_time:.2f} & {r.average_time:.2f} & {r.median_memory:.2f} & {r.average_memory:.2f} & {r.timeouts}/{r.ooms} \\\\"
        )


def build_lara_fn_breakdown_row(
    results_dir: Path,
    reported_sets: Dict[str, Set[Key]],
    v_union: Set[Key],
) -> FnBreakdownRow:
    fn_keys = sorted(v_union - reported_sets["ere"])
    ere_records = load_records_by_key(results_dir, "1_expr", "ere")

    timeout = 0
    oom = 0
    others = 0
    for key in fn_keys:
        ere_record = ere_records.get(key, {})
        reason = get_termination_reason(ere_record)
        if reason == "timeout":
            timeout += 1
        elif reason == "memory":
            oom += 1
        else:
            others += 1

    return FnBreakdownRow(
        tool="ere",
        total=len(fn_keys),
        timeout=timeout,
        oom=oom,
        others=others,
    )


def print_lara_fn_breakdown_table(row: FnBreakdownRow) -> None:
    print("\n=== Table: LARA FN Breakdown (tab:lara-fn) ===")
    print(f"{'Tool':<12} {'Total FN':>10} {'Timeout':>10} {'OOM':>8} {'Others':>10}")
    print(
        f"{TOOL_DISPLAY[row.tool]:<12} {row.total:>10} {row.timeout:>10} {row.oom:>8} {row.others:>10}"
    )


def print_confirmed_lara_fn_breakdown_table(row: FnBreakdownRow) -> None:
    print("\n=== Table: Confirmed CVE LARA FN Breakdown (tab:cve-lara-fn) ===")
    print(f"{'Tool':<12} {'Total FN':>10} {'Timeout':>10} {'OOM':>8} {'Others':>10}")
    print(
        f"{TOOL_DISPLAY[row.tool]:<12} {row.total:>10} {row.timeout:>10} {row.oom:>8} {row.others:>10}"
    )


def print_lara_fn_breakdown_latex(row: FnBreakdownRow) -> None:
    print("\nLaTeX rows for tab:lara-fn:")
    print(
        f"{TOOL_DISPLAY[row.tool]} & {row.total} & {row.timeout} & {row.oom} & {row.others} \\\\"
    )


def write_lara_fn_csv(
    results_dir: Path,
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
    output_csv: Path,
) -> None:
    fn_keys = sorted(v_union - reported_sets["ere"])
    ere_records = load_records_by_key(results_dir, "1_expr", "ere")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "line",
                "input",
                "input_length",
                "verified_engines",
                "detected_by_other_tools",
                "verified_by_tools",
                "verified_attack_details",
                "ere_output",
                "ere_stdout",
                "ere_stderr",
                "ere_return_code",
                "ere_timeout_flag",
                "ere_is_timeout_record",
                "ere_is_oom_record",
                "ere_record_json",
            ],
        )
        writer.writeheader()

        for key in fn_keys:
            ere_record = ere_records.get(key, {})
            verified_engines = [
                ENGINE_DISPLAY[eng]
                for eng in ENGINES
                if any(key in attacks_by_engine[eng][tool] for tool in TOOLS)
            ]
            detected_by_other_tools = [
                TOOL_DISPLAY[tool]
                for tool in TOOLS
                if tool != "ere" and key in reported_sets[tool]
            ]
            verified_by_tools = [
                TOOL_DISPLAY[tool]
                for tool in TOOLS
                if any(key in attacks_by_engine[eng][tool] for eng in ENGINES)
            ]
            verified_attack_details = [
                f"{TOOL_DISPLAY[tool]}:{'/'.join(ENGINE_DISPLAY[eng] for eng in ENGINES if key in attacks_by_engine[eng][tool])}"
                for tool in TOOLS
                if any(key in attacks_by_engine[eng][tool] for eng in ENGINES)
            ]
            writer.writerow(
                {
                    "file": key[0],
                    "line": key[1],
                    "input": ere_record.get("input", ""),
                    "input_length": len(str(ere_record.get("input", ""))),
                    "verified_engines": "; ".join(verified_engines),
                    "detected_by_other_tools": "; ".join(detected_by_other_tools),
                    "verified_by_tools": "; ".join(verified_by_tools),
                    "verified_attack_details": "; ".join(verified_attack_details),
                    "ere_output": ere_record.get("output", ""),
                    "ere_stdout": ere_record.get("stdout", ""),
                    "ere_stderr": ere_record.get("stderr", ""),
                    "ere_return_code": ere_record.get("return_code", ""),
                    "ere_timeout_flag": ere_record.get("timeout", ""),
                    "ere_is_timeout_record": is_timeout_record(ere_record),
                    "ere_is_oom_record": is_oom_record(ere_record),
                    "ere_record_json": json.dumps(
                        ere_record, ensure_ascii=False, sort_keys=True
                    ),
                }
            )


def write_unique_detection_csv(
    results_dir: Path,
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
    output_csv: Path,
) -> None:
    unique_detection_sets, _ = build_unique_sets(
        reported_sets, attacks_by_engine, v_union
    )
    expr_records = {
        tool: load_records_by_key(results_dir, "1_expr", tool)
        for tool in TOOLS
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "line",
                "input",
                "input_length",
                "unique_tool",
                "unique_tool_display",
                "verified_engines",
                "detected_by_tools",
                "detected_by_other_tools",
                "verified_by_tools",
                "verified_attack_details",
                "owner_output",
                "owner_stdout",
                "owner_stderr",
                "owner_return_code",
                "owner_timeout_flag",
                "owner_is_timeout_record",
                "owner_is_oom_record",
                "owner_record_json",
            ],
        )
        writer.writeheader()

        for tool in TOOLS:
            for key in sorted(unique_detection_sets[tool], key=export_sort_key):
                owner_record = expr_records[tool].get(key, {})
                verified_engines = [
                    ENGINE_DISPLAY[eng]
                    for eng in ENGINES
                    if any(key in attacks_by_engine[eng][other_tool] for other_tool in TOOLS)
                ]
                detected_by_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if key in reported_sets[other_tool]
                ]
                detected_by_other_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if other_tool != tool and key in reported_sets[other_tool]
                ]
                verified_by_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if any(key in attacks_by_engine[eng][other_tool] for eng in ENGINES)
                ]
                verified_attack_details = [
                    f"{TOOL_DISPLAY[other_tool]}:{'/'.join(ENGINE_DISPLAY[eng] for eng in ENGINES if key in attacks_by_engine[eng][other_tool])}"
                    for other_tool in TOOLS
                    if any(key in attacks_by_engine[eng][other_tool] for eng in ENGINES)
                ]
                writer.writerow(
                    {
                        "file": key[0],
                        "line": key[1],
                        "input": owner_record.get("input", ""),
                        "input_length": len(str(owner_record.get("input", ""))),
                        "unique_tool": tool,
                        "unique_tool_display": TOOL_DISPLAY[tool],
                        "verified_engines": "; ".join(verified_engines),
                        "detected_by_tools": "; ".join(detected_by_tools),
                        "detected_by_other_tools": "; ".join(detected_by_other_tools),
                        "verified_by_tools": "; ".join(verified_by_tools),
                        "verified_attack_details": "; ".join(verified_attack_details),
                        "owner_output": owner_record.get("output", ""),
                        "owner_stdout": owner_record.get("stdout", ""),
                        "owner_stderr": owner_record.get("stderr", ""),
                        "owner_return_code": owner_record.get("return_code", ""),
                        "owner_timeout_flag": owner_record.get("timeout", ""),
                        "owner_is_timeout_record": is_timeout_record(owner_record),
                        "owner_is_oom_record": is_oom_record(owner_record),
                        "owner_record_json": json.dumps(
                            owner_record, ensure_ascii=False, sort_keys=True
                        ),
                    }
                )


def write_unique_attack_csv(
    results_dir: Path,
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
    output_csv: Path,
) -> None:
    _, unique_attack_sets = build_unique_sets(reported_sets, attacks_by_engine, v_union)
    expr_records = {
        tool: load_records_by_key(results_dir, "1_expr", tool)
        for tool in TOOLS
    }
    detect_records = {
        eng: {
            tool: load_records_by_key(results_dir / eng, "1_detect", tool)
            for tool in TOOLS
        }
        for eng in ENGINES
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "line",
                "input",
                "input_length",
                "unique_tool",
                "unique_tool_display",
                "detected_by_tools",
                "detected_by_other_tools",
                "verified_by_tools",
                "verified_by_other_tools",
                "owner_verified_engines",
                "owner_verified_engine_count",
                "owner_attack_details",
                *[f"{eng}_verified" for eng in ENGINES],
                *[f"{eng}_record_json" for eng in ENGINES],
                "owner_expr_record_json",
            ],
        )
        writer.writeheader()

        for tool in TOOLS:
            for key in sorted(unique_attack_sets[tool], key=export_sort_key):
                owner_expr_record = expr_records[tool].get(key, {})
                detected_by_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if key in reported_sets[other_tool]
                ]
                detected_by_other_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if other_tool != tool and key in reported_sets[other_tool]
                ]
                verified_by_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if any(key in attacks_by_engine[eng][other_tool] for eng in ENGINES)
                ]
                verified_by_other_tools = [
                    TOOL_DISPLAY[other_tool]
                    for other_tool in TOOLS
                    if other_tool != tool and any(key in attacks_by_engine[eng][other_tool] for eng in ENGINES)
                ]
                owner_verified_engines = [
                    ENGINE_DISPLAY[eng]
                    for eng in ENGINES
                    if key in attacks_by_engine[eng][tool]
                ]
                owner_attack_details = [
                    f"{ENGINE_DISPLAY[eng]}:{'success' if key in attacks_by_engine[eng][tool] else 'no-success'}"
                    for eng in ENGINES
                ]

                row = {
                    "file": key[0],
                    "line": key[1],
                    "input": owner_expr_record.get("input", ""),
                    "input_length": len(str(owner_expr_record.get("input", ""))),
                    "unique_tool": tool,
                    "unique_tool_display": TOOL_DISPLAY[tool],
                    "detected_by_tools": "; ".join(detected_by_tools),
                    "detected_by_other_tools": "; ".join(detected_by_other_tools),
                    "verified_by_tools": "; ".join(verified_by_tools),
                    "verified_by_other_tools": "; ".join(verified_by_other_tools),
                    "owner_verified_engines": "; ".join(owner_verified_engines),
                    "owner_verified_engine_count": len(owner_verified_engines),
                    "owner_attack_details": "; ".join(owner_attack_details),
                    "owner_expr_record_json": json.dumps(
                        owner_expr_record, ensure_ascii=False, sort_keys=True
                    ),
                }
                for eng in ENGINES:
                    row[f"{eng}_verified"] = key in attacks_by_engine[eng][tool]
                    row[f"{eng}_record_json"] = json.dumps(
                        detect_records[eng][tool].get(key, {}),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                writer.writerow(row)


def write_confirmed_lara_fn_csv(
    results_dir: Path,
    reported_sets: Dict[str, Set[Key]],
    reference_records: Dict[Key, dict],
    tools: Iterable[str],
    output_csv: Path,
) -> None:
    fn_keys = sorted(set(reference_records) - reported_sets["ere"])
    ere_records = load_records_by_key(results_dir, "1_expr", "ere")
    tool_list = list(tools)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "line",
                "input",
                "input_length",
                "detected_by_other_tools",
                "detected_by_other_tools_count",
                "termination_reason",
                "ere_output",
                "ere_stdout",
                "ere_stderr",
                "ere_return_code",
                "ere_timeout_flag",
                "ere_is_timeout_record",
                "ere_is_oom_record",
                "ere_record_json",
            ],
        )
        writer.writeheader()

        for key in fn_keys:
            ere_record = ere_records.get(key, reference_records.get(key, {}))
            detected_by_other_tools = [
                TOOL_DISPLAY[tool]
                for tool in tool_list
                if tool != "ere" and key in reported_sets[tool]
            ]
            writer.writerow(
                {
                    "file": key[0],
                    "line": key[1],
                    "input": ere_record.get("input", ""),
                    "input_length": len(str(ere_record.get("input", ""))),
                    "detected_by_other_tools": "; ".join(detected_by_other_tools),
                    "detected_by_other_tools_count": len(detected_by_other_tools),
                    "termination_reason": get_termination_reason(ere_record) or "other",
                    "ere_output": ere_record.get("output", ""),
                    "ere_stdout": ere_record.get("stdout", ""),
                    "ere_stderr": ere_record.get("stderr", ""),
                    "ere_return_code": ere_record.get("return_code", ""),
                    "ere_timeout_flag": ere_record.get("timeout", ""),
                    "ere_is_timeout_record": is_timeout_record(ere_record),
                    "ere_is_oom_record": is_oom_record(ere_record),
                    "ere_record_json": json.dumps(
                        ere_record, ensure_ascii=False, sort_keys=True
                    ),
                }
            )


def plot_detection_stackbar(
    reported_sets: Dict[str, Set[Key]],
    v_union: Set[Key],
    output_pdf: Path,
    our_tool: str = "ere",
) -> None:
    rows = build_detection_stackbar_rows(reported_sets, v_union, our_tool=our_tool)
    if not rows:
        raise ValueError("No baseline tools to compare against.")

    labels = [TOOL_DISPLAY[r.tool] for r in rows]
    seg_other_found = [r.other_tools_found for r in rows]
    seg_only_other = [r.only_other_tool for r in rows]
    seg_both = [r.both_found for r in rows]
    seg_only_ours = [r.only_lara_found for r in rows]

    counts = np.array(
        [seg_other_found, seg_only_other, seg_both, seg_only_ours], dtype=float
    )
    totals = counts.sum(axis=0)
    totals[totals == 0] = 1.0

    # 与 draw_cactus.py 一致的视觉补偿：极小非零块给最小可见高度
    pct = counts / totals * 100.0
    min_vis_pct = PLOT_STACKBAR_MIN_VISIBLE_PCT
    vis_pct = pct.copy()
    vis_pct[(vis_pct > 0) & (vis_pct < min_vis_pct)] = min_vis_pct
    vis_totals = vis_pct.sum(axis=0)
    vis_totals[vis_totals == 0] = 1.0
    vis_pct = vis_pct / vis_totals * 100.0

    colors = ["#eeeeee", "#f8cecc", "#fff2cc", "#dae8fc"]
    legend_labels = [
        "Other Tools Found",
        "Only Other Tool",
        "Both Found",
        "Only LARA Found",
    ]

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=PLOT_STACKBAR_FIGSIZE)

    x = np.arange(len(labels))
    bottom = np.zeros(len(labels), dtype=float)
    bars = []

    for i in range(4):
        bar = ax.bar(
            x,
            vis_pct[i],
            bottom=bottom,
            color=colors[i],
            edgecolor="#444444",
            linewidth=0.5,
            width=0.7,
            label=legend_labels[i],
        )
        bars.append(bar)
        bottom += vis_pct[i]

    # 标注原始计数
    for i, bar_group in enumerate(bars):
        labels_count = [f"{int(v)}" if v > 0 else "" for v in counts[i]]
        ax.bar_label(
            bar_group,
            labels=labels_count,
            label_type="center",
            fontsize=PLOT_STACKBAR_ANNOTATION_FONTSIZE,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, fontsize=PLOT_STACKBAR_TICK_FONTSIZE)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage over Set V (%)", fontsize=PLOT_STACKBAR_LABEL_FONTSIZE)
    ax.set_xlabel("Pairwise Comparison with LARA", fontsize=PLOT_STACKBAR_LABEL_FONTSIZE)
    ax.tick_params(axis="y", labelsize=PLOT_STACKBAR_TICK_FONTSIZE)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=2,
        frameon=False,
        fontsize=PLOT_STACKBAR_LEGEND_FONTSIZE,
        columnspacing=1.2,
        handletextpad=0.6,
        labelspacing=0.35,
    )

    # fig.subplots_adjust(left=0.15, right=0.94, bottom=0.14, top=0.8)
    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close(fig)


def plot_detection_upset(
    reported_sets: Dict[str, Set[Key]],
    v_union: Set[Key],
    output_pdf: Path,
) -> None:
    if not v_union:
        raise ValueError("Global verified set V is empty, cannot build detection upset plot.")

    det_sets: Dict[str, Set[Key]] = {t: (reported_sets[t] & v_union) for t in TOOLS}
    display_tools = [TOOL_DISPLAY[t] for t in TOOLS]
    set_sizes = [len(det_sets[t]) for t in TOOLS]
    bool_rows = []
    uncovered = 0

    for key in v_union:
        row = {}
        hit_any = False
        for tool in TOOLS:
            present = key in det_sets[tool]
            row[TOOL_DISPLAY[tool]] = present
            hit_any = hit_any or present
        if hit_any:
            bool_rows.append(row)
        else:
            uncovered += 1

    if not bool_rows:
        raise ValueError("No confirmed vulnerabilities are covered by any detector in V.")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    def _plot_upset_fallback(rows: List[Dict[str, bool]], out_pdf: Path, not_detected: int) -> None:
        combo_counts: Dict[Tuple[bool, ...], int] = {}
        for row in rows:
            key = tuple(row[t] for t in display_tools)
            combo_counts[key] = combo_counts.get(key, 0) + 1

        combos = sorted(
            combo_counts.items(),
            key=lambda item: (-item[1], -sum(item[0]), item[0]),
        )
        if not combos:
            raise ValueError("No non-empty intersections available for UpSet fallback.")

        combo_keys = [k for k, _ in combos]
        counts = [v for _, v in combos]
        n_cols = len(combo_keys)
        n_tools = len(display_tools)
        max_set_size = max(set_sizes) if set_sizes else 0

        label_panel_width = 1.65
        right_panel_width = max(4.8, 0.14 * n_cols + 1.6)
        fig_width = max(PLOT_UPSET_FIGSIZE[0], 3.8 + label_panel_width + right_panel_width)
        fig_height = max(PLOT_UPSET_FIGSIZE[1], 4.6 + 0.45 * n_tools)
        fig = plt.figure(figsize=(fig_width, fig_height))
        gs = fig.add_gridspec(
            2,
            3,
            height_ratios=[2.5, 2.0],
            width_ratios=[3.6, label_panel_width, right_panel_width],
            hspace=0.04,
            wspace=0.03,
        )
        ax_blank = fig.add_subplot(gs[0, 0:2])
        ax_bar = fig.add_subplot(gs[0, 2])
        ax_sets = fig.add_subplot(gs[1, 0])
        ax_labels = fig.add_subplot(gs[1, 1])
        ax_mat = fig.add_subplot(gs[1, 2], sharex=ax_bar, sharey=ax_sets)

        ax_blank.axis("off")

        x = np.arange(n_cols)
        ax_bar.bar(
            x,
            counts,
            width=0.55,
            color="#4e79a7",
            edgecolor="#2f3e4e",
            linewidth=0.5,
        )
        ax_bar.set_ylabel("Intersection Size", fontsize=PLOT_LABEL_FONTSIZE)
        ax_bar.tick_params(axis="y", labelsize=PLOT_TICK_FONTSIZE)
        ax_bar.grid(axis="y", linestyle="--", alpha=0.4)
        ax_bar.set_axisbelow(True)
        ax_bar.tick_params(axis="x", labelbottom=False, bottom=False)
        ax_bar.set_xlim(-0.5, n_cols - 0.5)
        ax_bar.spines["top"].set_visible(False)
        ax_bar.spines["right"].set_visible(False)

        y_positions = np.arange(n_tools)
        for row_idx in y_positions:
            if row_idx % 2 == 1:
                ax_sets.axhspan(row_idx - 0.5, row_idx + 0.5, color="#f7f7f7", zorder=0)
                ax_labels.axhspan(row_idx - 0.5, row_idx + 0.5, color="#f7f7f7", zorder=0)
                ax_mat.axhspan(row_idx - 0.5, row_idx + 0.5, color="#f7f7f7", zorder=0)

        ax_sets.barh(
            y_positions,
            [-size for size in set_sizes],
            height=0.46,
            color="#4e79a7",
            edgecolor="#2f3e4e",
            linewidth=0.5,
            zorder=2,
        )
        label_offset = max(max_set_size * 0.035, 8)
        for y, size in zip(y_positions, set_sizes):
            ax_sets.text(
                -size - label_offset,
                y,
                str(size),
                ha="right",
                va="center",
                fontsize=PLOT_LABEL_FONTSIZE,
            )

        ax_sets.set_yticks(y_positions)
        ax_sets.set_yticklabels([])
        ax_sets.tick_params(axis="y", left=False, right=False, length=0)
        ax_sets.tick_params(axis="x", bottom=False, labelbottom=False)
        ax_sets.set_xlim(-(max_set_size * 1.32 + label_offset), 0)
        ax_sets.set_ylim(-0.5, n_tools - 0.5)
        ax_sets.invert_yaxis()
        ax_sets.set_title("Reference Coverage", fontsize=PLOT_LABEL_FONTSIZE, pad=8)
        for spine in ["top", "left", "bottom", "right"]:
            ax_sets.spines[spine].set_visible(False)

        ax_labels.set_xlim(0, 1)
        ax_labels.set_ylim(ax_sets.get_ylim())
        ax_labels.set_xticks([])
        ax_labels.set_yticks([])
        ax_labels.tick_params(
            axis="both",
            which="both",
            left=False,
            right=False,
            bottom=False,
            top=False,
            labelleft=False,
            labelbottom=False,
            length=0,
        )
        for y, label in zip(y_positions, display_tools):
            ax_labels.text(
                0.02,
                y,
                label,
                ha="left",
                va="center",
                fontsize=PLOT_LABEL_FONTSIZE,
                clip_on=False,
            )
        for spine in ["top", "left", "bottom", "right"]:
            ax_labels.spines[spine].set_visible(False)
        ax_labels.set_frame_on(False)

        for col_idx, combo in enumerate(combo_keys):
            ax_mat.scatter(
                np.full(n_tools, col_idx),
                y_positions,
                s=18,
                color="#d9d9d9",
                zorder=1,
            )
            present_rows = [i for i, v in enumerate(combo) if v]
            if present_rows:
                ax_mat.scatter(
                    np.full(len(present_rows), col_idx),
                    np.array(present_rows),
                    s=24,
                    color="#222222",
                    zorder=2,
                )
                if len(present_rows) > 1:
                    ax_mat.plot(
                        [col_idx, col_idx],
                        [min(present_rows), max(present_rows)],
                        color="#222222",
                        linewidth=0.9,
                        zorder=1.5,
                    )

        ax_mat.set_xlim(-0.6, n_cols - 0.4)
        ax_mat.set_xticks([])
        ax_mat.set_yticks(y_positions)
        ax_mat.tick_params(axis="y", left=False, labelleft=False)
        ax_mat.tick_params(axis="x", bottom=False, labelbottom=False)
        ax_mat.spines["top"].set_visible(False)
        ax_mat.spines["right"].set_visible(False)
        ax_mat.spines["bottom"].set_visible(False)
        ax_mat.spines["left"].set_visible(False)

        if not_detected > 0:
            fig.text(
                0.01,
                0.01,
                f"Not detected by any tool in V: {not_detected}",
                fontsize=PLOT_ANNOTATION_FONTSIZE,
                ha="left",
                va="bottom",
            )

        fig.subplots_adjust(left=0.05, right=0.995, bottom=0.08, top=0.98)
        plt.savefig(out_pdf)
        plt.close(fig)

    _plot_upset_fallback(bool_rows, output_pdf, uncovered)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate detection/attack tables from expr results for paper reporting."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Results root, containing 1_expr*.json and engine subdirs.",
    )
    args = parser.parse_args()

    results_dir = args.results_dir
    if is_cve_results_dir(results_dir):
        run_confirmed_only_mode(results_dir)
        return

    run_standard_mode(results_dir)

    if results_dir == DEFAULT_RESULTS_DIR and DEFAULT_CVE_RESULTS_DIR.exists():
        print("\n=== Confirmed CVE Tables ===")
        run_confirmed_only_mode(DEFAULT_CVE_RESULTS_DIR)


if __name__ == "__main__":
    main()
