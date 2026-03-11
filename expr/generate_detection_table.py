#!/usr/bin/env python3
import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Set, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import re

TOOLS: List[str] = ["ere", "redoshunter", "rengar", "revealer", "rescue"]
TOOL_DISPLAY = {
    "ere": "LARA",
    "redoshunter": "ReDoSHunter",
    "rengar": "Rengar",
    "revealer": "Revealer",
    "rescue": "ReScue",
}
ENGINES: List[str] = ["nodejs14", "python", "java11"]
ENGINE_DISPLAY = {"nodejs14": "Node.js", "python": "Python", "java11": "Java"}

EXPECTED_COUNTS = {
    "nodejs14": 4415,
    "python": 4507,
    "java11": 5354,
    "union": 5847,
}

Key = Tuple[str, int]


@dataclass
class DetectionRow:
    tool: str
    reported: int
    det_recall: float
    missed: int
    unconfirmed: int


@dataclass
class AttackUnionRow:
    tool: str
    successful_attacks: int
    attack_recall: float
    attack_conversion: float


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
class PerformanceRow:
    tool: str
    median_time: float
    average_time: float
    median_memory: float
    average_memory: float
    timeouts: int
    ooms: int


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


def is_timeout_record(record: dict) -> bool:
    if record.get("timeout", False) is True:
        return True
    stdout = str(record.get("stdout", ""))
    return (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    )


def is_oom_record(record: dict) -> bool:
    stdout = str(record.get("stdout", ""))
    return "terminationreason=memory" in stdout


def find_file(root: Path, prefix: str, tool: str) -> Path:
    direct = root / f"{prefix}_{tool}.json"
    if direct.exists():
        return direct

    # 兼容 .jsonl 或其他后缀
    candidates = sorted(root.glob(f"{prefix}_{tool}.json*"))
    if not candidates:
        raise FileNotFoundError(f"Missing file for tool={tool}: {root / (prefix + '_' + tool + '.json*')}")
    return candidates[0]


def load_reported_sets(results_dir: Path) -> Dict[str, Set[Key]]:
    reported: Dict[str, Set[Key]] = {t: set() for t in TOOLS}
    for tool in TOOLS:
        path = find_file(results_dir, "1_expr", tool)
        for rec in iter_json_objects(path):
            if claims_redos(rec):
                reported[tool].add(parse_key(rec))
    return reported


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
    print(f"{'Tool':<12} {'Reported':>10} {'Detection Recall':>18} {'Missed':>10} {'Unconfirmed':>14}")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<12} {r.reported:>10} {format_pct(r.det_recall):>18} {r.missed:>10} {r.unconfirmed:>14}"
        )


def print_detection_latex(rows: List[DetectionRow]) -> None:
    print("\\nLaTeX rows for tab:detection:")
    for r in rows:
        line = (
            f"{TOOL_DISPLAY[r.tool]} & {r.reported} & {r.det_recall * 100:.2f}\\%"
            f" & {r.missed} & {r.unconfirmed} \\\\" 
        )
        print(line)


def print_attack_all(attacks_by_engine: Dict[str, Dict[str, Set[Key]]], v_union: Set[Key]) -> None:
    print("\\n=== Attack Success Count by Engine (for tab:attack-all) ===")
    print(f"{'Tool':<12} {'Node.js':>8} {'Python':>8} {'Java':>8} {'At least one':>13}")
    for tool in TOOLS:
        node_n = len(attacks_by_engine["nodejs14"][tool])
        py_n = len(attacks_by_engine["python"][tool])
        java_n = len(attacks_by_engine["java11"][tool])
        union_n = len(
            attacks_by_engine["nodejs14"][tool]
            | attacks_by_engine["python"][tool]
            | attacks_by_engine["java11"][tool]
        )
        print(f"{TOOL_DISPLAY[tool]:<12} {node_n:>8} {py_n:>8} {java_n:>8} {union_n:>13}")

    print("-" * 56)
    print(
        f"{'Marked total':<12} {len(set().union(*attacks_by_engine['nodejs14'].values())):>8}"
        f" {len(set().union(*attacks_by_engine['python'].values())):>8}"
        f" {len(set().union(*attacks_by_engine['java11'].values())):>8}"
        f" {len(v_union):>13}"
    )


def print_attack_union(rows: List[AttackUnionRow]) -> None:
    print("\\n=== Attack Union Summary (for tab:attack-union) ===")
    print(f"{'Tool':<12} {'Successful Attacks':>20} {'Attack Recall':>14} {'Conversion':>12}")
    for r in rows:
        print(
            f"{TOOL_DISPLAY[r.tool]:<12} {r.successful_attacks:>20} {format_pct(r.attack_recall):>14} {format_pct(r.attack_conversion):>12}"
        )


def print_verify_counts(v_engine: Dict[str, Set[Key]], v_union: Set[Key]) -> None:
    print("\\n=== Verify Marked Counts (paper numbers) ===")
    actual = {
        "nodejs14": len(v_engine["nodejs14"]),
        "python": len(v_engine["python"]),
        "java11": len(v_engine["java11"]),
        "union": len(v_union),
    }

    for k in ["nodejs14", "python", "java11", "union"]:
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


def build_unique_rows(
    reported_sets: Dict[str, Set[Key]],
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
) -> List[UniqueRow]:
    detection_hits: Dict[str, Set[Key]] = {t: (reported_sets[t] & v_union) for t in TOOLS}
    attack_union_sets: Dict[str, Set[Key]] = {
        t: (
            attacks_by_engine["nodejs14"][t]
            | attacks_by_engine["python"][t]
            | attacks_by_engine["java11"][t]
        )
        for t in TOOLS
    }

    rows: List[UniqueRow] = []
    for tool in TOOLS:
        other_detection_union = set().union(
            *[detection_hits[t] for t in TOOLS if t != tool]
        )
        other_attack_union = set().union(
            *[attack_union_sets[t] for t in TOOLS if t != tool]
        )
        rows.append(
            UniqueRow(
                tool=tool,
                unique_detections=len(detection_hits[tool] - other_detection_union),
                unique_attacks=len(attack_union_sets[tool] - other_attack_union),
            )
        )
    return rows


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
        t: (
            attacks_by_engine["nodejs14"][t]
            | attacks_by_engine["python"][t]
            | attacks_by_engine["java11"][t]
        )
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
        t: (
            attacks_by_engine["nodejs14"][t]
            | attacks_by_engine["python"][t]
            | attacks_by_engine["java11"][t]
        )
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
    fig, ax = plt.subplots(figsize=(12, 8))
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

    ax.set_title(f"{title} ({mode_desc})", fontsize=14)
    ax.set_xlabel("Number of Solved Instances", fontsize=12)
    ax.set_ylabel(f"{y_label} - Log Scale", fontsize=12)
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
        fontsize=10,
        ha="right",
        va="bottom",
        transform=ax.get_yaxis_transform(),
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.5},
    )
    ax.grid(True, which="major", ls="-", alpha=0.4)
    ax.grid(True, which="minor", ls=":", alpha=0.2)
    ax.legend(loc="lower right")

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
    min_vis_pct = 2.0
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
    fig, ax = plt.subplots(figsize=(10, 6))
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
        ax.bar_label(bar_group, labels=labels_count, label_type="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage over Attack Success Union (%)")
    ax.set_xlabel("Pairwise Comparison with LARA")
    ax.set_title("Attack Overlap (Pairwise): LARA vs Baselines")
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=4, frameon=False)

    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close(fig)


def print_without_lara_stats(
    attacks_by_engine: Dict[str, Dict[str, Set[Key]]],
    v_union: Set[Key],
) -> None:
    baseline_union = set().union(
        *[
            attacks_by_engine["nodejs14"][t]
            | attacks_by_engine["python"][t]
            | attacks_by_engine["java11"][t]
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
    min_vis_pct = 2.0
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
    fig, ax = plt.subplots(figsize=(10, 6))

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
        ax.bar_label(bar_group, labels=labels_count, label_type="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage over Verified Vulnerability Set V (%)")
    ax.set_xlabel("Pairwise Comparison with LARA")
    ax.set_title("Detection Effect (Pairwise): LARA vs Baselines")
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=4, frameon=False)

    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate detection/attack tables from expr results for paper reporting."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("expr/results"),
        help="Results root, containing 1_expr*.json and engine subdirs.",
    )
    args = parser.parse_args()

    results_dir = args.results_dir

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
        recall = (hit / len(v_union)) if v_union else 0.0
        missed = len(v_union - r_set)
        unconfirmed = len(r_set - v_union)
        detection_rows.append(
            DetectionRow(
                tool=tool,
                reported=reported,
                det_recall=recall,
                missed=missed,
                unconfirmed=unconfirmed,
            )
        )

    # Attack union table metrics
    attack_union_rows: List[AttackUnionRow] = []
    for tool in TOOLS:
        a_union = (
            attacks_by_engine["nodejs14"][tool]
            | attacks_by_engine["python"][tool]
            | attacks_by_engine["java11"][tool]
        )
        reported = len(reported_sets[tool])
        attack_union_rows.append(
            AttackUnionRow(
                tool=tool,
                successful_attacks=len(a_union),
                attack_recall=(len(a_union) / len(v_union)) if v_union else 0.0,
                attack_conversion=(len(a_union) / reported) if reported else 0.0,
            )
        )

    # Print outputs
    print_detection_table(detection_rows)
    print_detection_latex(detection_rows)
    print_attack_all(attacks_by_engine, v_union)
    print_attack_union(attack_union_rows)
    print_verify_counts(v_engine, v_union)
    print_detection_stackbar_table(
        build_detection_stackbar_rows(reported_sets, v_union, our_tool="ere")
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

    detection_fig = results_dir.parent / "plots" / "detection_stackbar.pdf"
    plot_detection_stackbar(reported_sets, v_union, detection_fig, our_tool="ere")
    print(f"\nSaved detection stackbar PDF: {detection_fig}")
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


if __name__ == "__main__":
    main()
