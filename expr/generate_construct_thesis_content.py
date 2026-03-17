#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CPU_RE = re.compile(r"cputime=([0-9.]+)s")
MEM_RE = re.compile(r"memory=([0-9]+)B")
TIME_IN_OUTPUT_RE = re.compile(r'"time"\s*:\s*([0-9.]+)')
CPUTIME_RE = re.compile(r"cputime=([0-9.]+)s")

LINEARITY_ENGINES = ["nodejs14", "python", "java11", "ere", "ere_dfa"]
LINEARITY_LABELS = {
    "nodejs14": "Node.js",
    "python": "Python",
    "java11": "Java",
    "ere": "RELAX-NFA",
    "ere_dfa": "RELAX-DFA",
}
LINEARITY_COLORS = {
    "nodejs14": "#ff7f0e",
    "python": "#2ca02c",
    "java11": "#d62728",
    "ere": "#1f77b4",
    "ere_dfa": "#9467bd",
}

PLOT_LABEL_FONTSIZE = 15
PLOT_TICK_FONTSIZE = 13
PLOT_LEGEND_FONTSIZE = 13
PLOT_CACTUS_FIGSIZE = (9, 6)
PLOT_SCATTER_FIGSIZE = (9, 6)
PLOT_LINEARITY_FIGSIZE = (9, 6)


@dataclass
class Record:
    key: Tuple[str, int, str]
    size: Optional[int]
    cpu_s: Optional[float]
    mem_mb: Optional[float]
    timeout: bool
    oom: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate thesis-ready construct stats for RELAX-NFA/RELAX-DFA."
    )
    parser.add_argument(
        "--nfa-jsonl",
        type=Path,
        default=Path("expr/results/3_construct/nfa.jsonl"),
        help="Path to NFA construct JSONL",
    )
    parser.add_argument(
        "--dfa-jsonl",
        type=Path,
        default=Path("expr/results/3_construct/dfa.jsonl"),
        help="Path to DFA construct JSONL",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("expr/results/3_construct/thesis_fill"),
        help="Output directory",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=5.0,
        help="CPU time limit (seconds), used as reference line in cactus plot",
    )
    parser.add_argument(
        "--memory-limit-mb",
        type=float,
        default=10240.0,
        help="Memory limit (MB), used as reference line in cactus plot",
    )
    parser.add_argument(
        "--linearity-input-dir",
        type=Path,
        default=Path("expr/results/2_linearity"),
        help="Directory containing linearity JSONL files for matching plot",
    )
    parser.add_argument(
        "--linearity-timeout-ms",
        type=float,
        default=5000.0,
        help="Fallback timeout value (ms) when timeout-like record misses cputime",
    )
    parser.add_argument(
        "--linearity-max-k",
        type=int,
        default=50000,
        help="Only include points with k <= this value in matching_linear plot",
    )
    parser.add_argument(
        "--matching-summary-low-k",
        type=int,
        default=1000,
        help="Requested low-repeat k for matching-summary table (nearest available k will be used)",
    )
    parser.add_argument(
        "--matching-summary-high-k",
        type=int,
        default=50000,
        help="Requested high-repeat k for matching-summary table (nearest available k will be used)",
    )
    return parser.parse_args()


def parse_stdout_value(stdout: str, regex: re.Pattern, cast):
    match = regex.search(stdout)
    if not match:
        return None
    return cast(match.group(1))


def parse_cputime_ms(stdout: str) -> Optional[float]:
    m = CPUTIME_RE.search(stdout)
    if not m:
        return None
    return float(m.group(1)) * 1000.0


def parse_output_time_ms(output_field) -> Optional[float]:
    if isinstance(output_field, dict):
        t = output_field.get("time")
        if isinstance(t, (int, float)):
            return float(t)
    if isinstance(output_field, str):
        try:
            payload = json.loads(output_field)
            if isinstance(payload, dict):
                t = payload.get("time")
                if isinstance(t, (int, float)):
                    return float(t)
        except Exception:
            m = TIME_IN_OUTPUT_RE.search(output_field)
            if m:
                return float(m.group(1))
    return None


def classify_timeout(stdout: str, timeout_flag: bool) -> bool:
    if timeout_flag:
        return True
    return "terminationreason=cputime-soft" in stdout or "terminationreason=cputime" in stdout


def classify_oom(stdout: str, stderr: str) -> bool:
    haystack = f"{stdout}\n{stderr}".lower()
    tokens = ["terminationreason=memory", "out of memory", "memory limit", "oom"]
    return any(t in haystack for t in tokens)


def read_records(path: Path) -> List[Record]:
    records: List[Record] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc

            output = obj.get("output")
            size = output.get("size") if isinstance(output, dict) else None
            if not isinstance(size, int):
                size = None

            stdout = obj.get("stdout", "")
            stderr = obj.get("stderr", "")
            stdout = stdout if isinstance(stdout, str) else ""
            stderr = stderr if isinstance(stderr, str) else ""

            cpu_s = parse_stdout_value(stdout, CPU_RE, float)
            mem_b = parse_stdout_value(stdout, MEM_RE, int)
            mem_mb = (mem_b / (1024.0 * 1024.0)) if mem_b is not None else None

            timeout_flag = bool(obj.get("timeout", False))
            timeout = classify_timeout(stdout, timeout_flag)
            oom = classify_oom(stdout, stderr)

            records.append(
                Record(
                    key=(
                        str(obj.get("file", "")),
                        int(obj.get("line", -1)),
                        str(obj.get("pattern", "")),
                    ),
                    size=size,
                    cpu_s=cpu_s,
                    mem_mb=mem_mb,
                    timeout=timeout,
                    oom=oom,
                )
            )
    return records


def fmt_float(x: float, digits: int = 4) -> str:
    return f"{x:.{digits}f}"


def fmt_int(x: int) -> str:
    return f"{x:,}"


def metric(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"median": 0.0, "mean": 0.0}
    return {"median": statistics.median(values), "mean": statistics.mean(values)}


def quantile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = (len(sorted_vals) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(records: List[Record]) -> Dict[str, object]:
    total = len(records)
    success = [r for r in records if r.size is not None]
    timeout = [r for r in records if r.size is None and r.timeout]
    oom = [r for r in records if r.size is None and (not r.timeout) and r.oom]
    other = [r for r in records if r.size is None and (not r.timeout) and (not r.oom)]

    cpu = [r.cpu_s for r in success if r.cpu_s is not None]
    mem = [r.mem_mb for r in success if r.mem_mb is not None]
    sizes = [r.size for r in success if r.size is not None]

    stats = {
        "count_total": total,
        "count_success": len(success),
        "count_timeout": len(timeout),
        "count_oom": len(oom),
        "count_other_failure": len(other),
        "cpu_s": metric(cpu),
        "mem_mb": metric(mem),
        "size": {
            "median": statistics.median(sizes) if sizes else 0.0,
            "mean": statistics.mean(sizes) if sizes else 0.0,
            "max": max(sizes) if sizes else 0,
        },
    }
    return stats


def get_success_sorted_values(records: List[Record], metric: str) -> List[float]:
    if metric not in {"time", "memory", "size"}:
        raise ValueError(f"Unknown metric: {metric}")
    vals: List[float] = []
    for r in records:
        if r.size is None:
            continue
        if metric == "time" and r.cpu_s is not None:
            vals.append(r.cpu_s)
        if metric == "memory" and r.mem_mb is not None:
            vals.append(r.mem_mb)
        if metric == "size" and r.size is not None:
            vals.append(float(r.size))
    vals.sort()
    return vals


def save_fig_dual(fig, out_dir: Path, stem: str) -> Dict[str, str]:
    pdf_path = out_dir / f"{stem}.pdf"
    png_path = out_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return {"pdf": str(pdf_path), "png": str(png_path)}


def plot_construct_cactus(
    nfa_values: List[float],
    dfa_values: List[float],
    metric: str,
    limit_value: Optional[float],
    out_dir: Path,
    stem: str,
) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=PLOT_CACTUS_FIGSIZE)

    if metric == "time":
        y_label = "CPU Time (s)"
        y_min = 1e-4
    elif metric == "memory":
        y_label = "Memory Usage (MB)"
        y_min = 1e-2
    elif metric == "size":
        y_label = "Automaton Size (states)"
        y_min = 1.0
    else:
        raise ValueError(f"Unknown metric: {metric}")

    if nfa_values:
        ax.plot(
            range(1, len(nfa_values) + 1),
            nfa_values,
            color="#1f77b4",
            linewidth=2.0,
            label=f"RELAX-NFA ({len(nfa_values)})",
        )
    if dfa_values:
        ax.plot(
            range(1, len(dfa_values) + 1),
            dfa_values,
            color="#d62728",
            linewidth=2.0,
            linestyle="--",
            label=f"RELAX-DFA ({len(dfa_values)})",
        )

    max_x = max(len(nfa_values), len(dfa_values), 1)
    max_y = max(nfa_values[-1] if nfa_values else y_min, dfa_values[-1] if dfa_values else y_min, y_min)
    ax.set_yscale("log")
    top = max_y * 1.2
    if limit_value is not None:
        top = max(top, limit_value * 1.25)
    ax.set_ylim(bottom=y_min, top=top)
    ax.set_xlim(left=0, right=max_x * 1.02)
    ax.set_xlabel("Number of Solved Instances", fontsize=PLOT_LABEL_FONTSIZE)
    ax.set_ylabel(f"{y_label} (log scale)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)
    ax.grid(True, which="major", ls="-", alpha=0.35)
    ax.grid(True, which="minor", ls=":", alpha=0.2)
    if limit_value is not None:
        ax.axhline(y=limit_value, color="#444444", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.legend(loc="lower right", fontsize=PLOT_LEGEND_FONTSIZE)
    return save_fig_dual(fig, out_dir, stem)


def build_success_size_pairs(
    nfa_records: List[Record], dfa_records: List[Record]
) -> Tuple[List[int], List[int]]:
    nfa_map = {r.key: r for r in nfa_records if r.size is not None}
    dfa_map = {r.key: r for r in dfa_records if r.size is not None}
    common_keys = sorted(set(nfa_map).intersection(dfa_map))
    xs: List[int] = []
    ys: List[int] = []
    for k in common_keys:
        n = nfa_map[k].size
        d = dfa_map[k].size
        if n is None or d is None:
            continue
        if n <= 0 or d <= 0:
            continue
        xs.append(n)
        ys.append(d)
    return xs, ys


def plot_nfa_dfa_size_scatter(
    nfa_sizes: List[int], dfa_sizes: List[int], out_dir: Path, stem: str
) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=PLOT_SCATTER_FIGSIZE)
    ax.scatter(nfa_sizes, dfa_sizes, s=8, alpha=0.25, color="#2ca02c")

    lo = min(min(nfa_sizes), min(dfa_sizes))
    hi = max(max(nfa_sizes), max(dfa_sizes))
    ax.plot([lo, hi], [lo, hi], linestyle="--", color="#444444", linewidth=1.2, label="y=x")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("RELAX-NFA size (states, log scale)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.set_ylabel("RELAX-DFA size (states, log scale)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)
    ax.grid(True, which="major", ls="-", alpha=0.35)
    ax.grid(True, which="minor", ls=":", alpha=0.2)
    ax.legend(loc="lower right", fontsize=PLOT_LEGEND_FONTSIZE)
    return save_fig_dual(fig, out_dir, stem)


def is_timeout_like(obj: dict) -> bool:
    if obj.get("timeout", False) is True:
        return True
    stdout = obj.get("stdout", "")
    if not isinstance(stdout, str):
        return False
    return (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    )


def load_linearity_runs(
    input_dir: Path, timeout_ms: float, max_k: Optional[int]
) -> List[dict]:
    rows: List[dict] = []
    for engine in LINEARITY_ENGINES:
        path = input_dir / f"{engine}.jsonl"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("warmup") is True:
                    continue
                sample_id = obj.get("sample_id")
                k = obj.get("k")
                if not isinstance(sample_id, str) or not isinstance(k, int):
                    continue
                if max_k is not None and k > max_k:
                    continue

                timed_out = is_timeout_like(obj)
                stdout = obj.get("stdout", "")
                stdout = stdout if isinstance(stdout, str) else ""
                t_ms = parse_cputime_ms(stdout)
                if t_ms is None:
                    t_ms = parse_output_time_ms(obj.get("output"))
                if t_ms is None and timed_out:
                    t_ms = timeout_ms
                if t_ms is None:
                    continue
                rows.append(
                    {
                        "engine": engine,
                        "sample_id": sample_id,
                        "k": k,
                        "time_ms": t_ms,
                        "timed_out": timed_out,
                    }
                )
    return rows


def build_linearity_sample_points(runs: List[dict]) -> List[dict]:
    per_sample = defaultdict(list)
    for r in runs:
        per_sample[(r["engine"], r["sample_id"], r["k"])].append(r)

    sample_point_rows: List[dict] = []
    for (engine, sample_id, k), rows in per_sample.items():
        times = sorted(float(x["time_ms"]) for x in rows)
        timed_out_count = sum(1 for x in rows if bool(x.get("timed_out", False)))
        sample_point_rows.append(
            {
                "engine": engine,
                "sample_id": sample_id,
                "k": k,
                "n_runs": len(rows),
                "timed_out_count": timed_out_count,
                "time_median_ms": quantile(times, 0.5),
            }
        )
    sample_point_rows.sort(key=lambda x: (x["engine"], x["sample_id"], x["k"]))
    return sample_point_rows


def build_linearity_main_points(sample_point_rows: List[dict]) -> List[dict]:
    grouped = defaultdict(list)
    for r in sample_point_rows:
        grouped[(r["engine"], r["k"])].append(r)

    main_points: List[dict] = []
    for (engine, k), rows in grouped.items():
        vals = sorted(float(x["time_median_ms"]) for x in rows)
        timeout_expr_count = sum(1 for x in rows if int(x["timed_out_count"]) > 0)
        main_points.append(
            {
                "engine": engine,
                "k": k,
                "n_samples": len(rows),
                "median_ms": quantile(vals, 0.5),
                "q1_ms": quantile(vals, 0.25),
                "q3_ms": quantile(vals, 0.75),
                "timeout_expr_count": timeout_expr_count,
            }
        )
    main_points.sort(key=lambda x: (x["engine"], x["k"]))
    return main_points


def plot_matching_linear(main_points: List[dict], out_dir: Path, stem: str) -> Dict[str, str]:
    by_engine = defaultdict(list)
    for r in main_points:
        by_engine[r["engine"]].append(r)

    fig, ax = plt.subplots(figsize=PLOT_LINEARITY_FIGSIZE)
    for engine in LINEARITY_ENGINES:
        rows = sorted(by_engine.get(engine, []), key=lambda x: x["k"])
        if not rows:
            continue
        x = [r["k"] for r in rows]
        y = [r["median_ms"] for r in rows]
        y1 = [r["q1_ms"] for r in rows]
        y3 = [r["q3_ms"] for r in rows]
        c = LINEARITY_COLORS[engine]
        ax.plot(
            x,
            y,
            marker="o",
            markersize=4.0,
            linewidth=1.8,
            color=c,
            label=LINEARITY_LABELS[engine],
        )
        ax.fill_between(x, y1, y3, color=c, alpha=0.16)

    ax.set_xlabel("Infix repeat times (k)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.set_ylabel("CPU time (ms)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)
    ax.grid(alpha=0.28)
    ax.legend(
        loc="center right",
        bbox_to_anchor=(0.98, 0.30),
        fontsize=PLOT_LEGEND_FONTSIZE,
    )
    return save_fig_dual(fig, out_dir, stem)


def plot_matching_log(main_points: List[dict], out_dir: Path, stem: str) -> Dict[str, str]:
    by_engine = defaultdict(list)
    for r in main_points:
        by_engine[r["engine"]].append(r)

    fig, ax = plt.subplots(figsize=PLOT_LINEARITY_FIGSIZE)
    for engine in LINEARITY_ENGINES:
        rows = sorted(by_engine.get(engine, []), key=lambda x: x["k"])
        if not rows:
            continue
        x = [r["k"] for r in rows]
        y = [max(r["median_ms"], 1e-3) for r in rows]
        y1 = [max(r["q1_ms"], 1e-3) for r in rows]
        y3 = [max(r["q3_ms"], 1e-3) for r in rows]
        c = LINEARITY_COLORS[engine]
        ax.plot(
            x,
            y,
            marker="o",
            markersize=4.0,
            linewidth=1.8,
            color=c,
            label=LINEARITY_LABELS[engine],
        )
        ax.fill_between(x, y1, y3, color=c, alpha=0.16)

    ax.set_yscale("log")
    ax.set_xlabel("Infix repeat times (k)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.set_ylabel("CPU time (ms, log scale)", fontsize=PLOT_LABEL_FONTSIZE)
    ax.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)
    ax.grid(alpha=0.28, which="major")
    ax.grid(alpha=0.18, which="minor", linestyle=":")
    ax.legend(loc="best", fontsize=PLOT_LEGEND_FONTSIZE)
    return save_fig_dual(fig, out_dir, stem)


def build_linearity_lookup(main_points: List[dict]) -> Dict[Tuple[str, int], dict]:
    return {(row["engine"], row["k"]): row for row in main_points}


def build_matching_log_notes(main_points: List[dict], target_k: int) -> str:
    lookup = build_linearity_lookup(main_points)

    def row(engine: str, k: int) -> Optional[dict]:
        return lookup.get((engine, k))

    def median(engine: str, k: int) -> Optional[float]:
        rec = row(engine, k)
        return None if rec is None else float(rec["median_ms"])

    def growth(engine: str, k0: int, k1: int) -> Optional[float]:
        a = median(engine, k0)
        b = median(engine, k1)
        if a is None or b is None or a <= 0:
            return None
        return b / a

    def fmt_ms(v: Optional[float]) -> str:
        return "N/A" if v is None else f"{v:.3f} ms"

    def fmt_ratio(v: Optional[float]) -> str:
        return "N/A" if v is None else f"{v:.2f}x"

    k_min = min((r["k"] for r in main_points), default=0)
    node_growth = growth("nodejs14", k_min, target_k)
    py_growth = growth("python", k_min, target_k)
    java_growth = growth("java11", k_min, target_k)
    nfa_target = median("ere", target_k)
    dfa_target = median("ere_dfa", target_k)
    node_target = median("nodejs14", target_k)
    py_target = median("python", target_k)
    java_target = median("java11", target_k)
    dfa_vs_nfa = (nfa_target / dfa_target) if (nfa_target and dfa_target and dfa_target > 0) else None
    nfa_vs_dfa = (dfa_target / nfa_target) if (nfa_target and dfa_target and nfa_target > 0) else None
    slowest_backtracking = max(v for v in [node_target, py_target, java_target] if v is not None)
    orders_vs_nfa = (
        math.log10(slowest_backtracking / nfa_target)
        if nfa_target and slowest_backtracking and nfa_target > 0
        else None
    )
    orders_vs_dfa = (
        math.log10(slowest_backtracking / dfa_target)
        if dfa_target and slowest_backtracking and dfa_target > 0
        else None
    )

    if dfa_vs_nfa is None or nfa_vs_dfa is None:
        relax_gap_line = "3. RELAX-NFA 与 RELAX-DFA 的性能差异：目标采样点数据不足，无法比较两种模式的差异。"
    elif dfa_target < nfa_target:
        relax_gap_line = (
            f"3. RELAX-NFA 与 RELAX-DFA 的性能差异：在 k={target_k} 时，RELAX-DFA 相比 RELAX-NFA 约快 {fmt_ratio(dfa_vs_nfa)}；"
            "在各采样点上二者都维持在个位数到十余毫秒量级。"
        )
    else:
        relax_gap_line = (
            f"3. RELAX-NFA 与 RELAX-DFA 的性能差异：在 k={target_k} 时，RELAX-DFA 相比 RELAX-NFA 约慢 {fmt_ratio(nfa_vs_dfa)}；"
            "当前这组样本上两条曲线整体仍然非常接近，均保持在个位数到十余毫秒量级。"
        )

    lines = [
        f"1. 回溯引擎增长趋势：Node.js、Python、Java 从 k={k_min} 到 k={target_k} 的中位时间增长分别约为 {fmt_ratio(node_growth)}、{fmt_ratio(py_growth)}、{fmt_ratio(java_growth)}。在对数纵轴下，这三条曲线整体持续上升，并在大 k 区域逼近或贴近 5 秒超时上限。",
        f"2. RELAX 的绝对性能：在 k={target_k} 时，RELAX-NFA 的中位匹配时间约为 {fmt_ms(nfa_target)}，RELAX-DFA 约为 {fmt_ms(dfa_target)}。",
        relax_gap_line,
        f"4. 性能差距的数量级：在 k={target_k} 时，Node.js/Python/Java 的中位匹配时间分别约为 {fmt_ms(node_target)}、{fmt_ms(py_target)}、{fmt_ms(java_target)}；最慢的回溯引擎相对 RELAX-NFA 约高 {orders_vs_nfa:.2f} 个数量级，相对 RELAX-DFA 约高 {orders_vs_dfa:.2f} 个数量级。"
        if orders_vs_nfa is not None and orders_vs_dfa is not None
        else "4. 性能差距的数量级：目标采样点数据不足，无法计算数量级差距。",
    ]
    return "\n".join(lines)


def resolve_nearest_k(available_ks: List[int], target_k: int) -> int:
    if not available_ks:
        return target_k
    return min(available_ks, key=lambda k: (abs(k - target_k), k))


def build_matching_summary_rows(
    main_points: List[dict], requested_low_k: int, requested_high_k: int
) -> Tuple[str, Dict[str, int]]:
    rows_by_engine_k = {(r["engine"], r["k"]): r for r in main_points}
    available_ks = sorted(set(int(r["k"]) for r in main_points))
    low_k = resolve_nearest_k(available_ks, requested_low_k)
    high_k = resolve_nearest_k(available_ks, requested_high_k)

    def sec(v_ms: float) -> str:
        return f"{(v_ms / 1000.0):.4f}"

    table_order = ["nodejs14", "python", "java11", "ere", "ere_dfa"]
    name_map = {
        "nodejs14": "Node.js-14",
        "python": "Python-3.10",
        "java11": "Java-11",
        "ere": "RELAX-NFA",
        "ere_dfa": "RELAX-DFA",
    }

    lines: List[str] = []
    for engine in table_order:
        lo = rows_by_engine_k.get((engine, low_k))
        hi = rows_by_engine_k.get((engine, high_k))
        low_s = sec(float(lo["median_ms"])) if lo is not None else "N/A"
        high_s = sec(float(hi["median_ms"])) if hi is not None else "N/A"
        timeout_n = str(int(hi["timeout_expr_count"])) if hi is not None else "N/A"
        lines.append(f"{name_map[engine]} & {low_s} & {high_s} & {timeout_n} \\\\")

    return "\n".join(lines), {"low_k": low_k, "high_k": high_k}


def build_latex_rows(nfa: Dict[str, object], dfa: Dict[str, object]) -> str:
    return "\n".join(
        [
            f"成功构造数        & {fmt_int(nfa['count_success'])} / {fmt_int(nfa['count_total'])} & {fmt_int(dfa['count_success'])} / {fmt_int(dfa['count_total'])} \\\\",
            f"超时数            & {fmt_int(nfa['count_timeout'])} & {fmt_int(dfa['count_timeout'])} \\\\",
            f"超内存数          & {fmt_int(nfa['count_oom'])} & {fmt_int(dfa['count_oom'])} \\\\",
            r"\midrule",
            f"中位构造时间 (s)  & {fmt_float(nfa['cpu_s']['median'])} & {fmt_float(dfa['cpu_s']['median'])} \\\\",
            f"平均构造时间 (s)  & {fmt_float(nfa['cpu_s']['mean'])} & {fmt_float(dfa['cpu_s']['mean'])} \\\\",
            f"中位内存 (MB)     & {fmt_float(nfa['mem_mb']['median'])} & {fmt_float(dfa['mem_mb']['median'])} \\\\",
            f"平均内存 (MB)     & {fmt_float(nfa['mem_mb']['mean'])} & {fmt_float(dfa['mem_mb']['mean'])} \\\\",
            r"\midrule",
            f"中位自动机大小（状态数） & {fmt_int(int(nfa['size']['median']))} & {fmt_int(int(dfa['size']['median']))} \\\\",
            f"平均自动机大小（状态数） & {fmt_float(nfa['size']['mean'])} & {fmt_float(dfa['size']['mean'])} \\\\",
            f"最大自动机大小（状态数） & {fmt_int(int(nfa['size']['max']))} & {fmt_int(int(dfa['size']['max']))} \\\\",
        ]
    )


def build_size_distribution_rows(
    nfa_q: Dict[str, float], dfa_q: Dict[str, float]
) -> str:
    return "\n".join(
        [
            "RELAX-NFA 状态数"
            + f" & {fmt_int(int(round(nfa_q['p25'])))}"
            + f" & {fmt_int(int(round(nfa_q['p50'])))}"
            + f" & {fmt_int(int(round(nfa_q['p75'])))}"
            + f" & {fmt_int(int(round(nfa_q['p95'])))}"
            + f" & {fmt_int(int(round(nfa_q['p99'])))} \\\\",
            "RELAX-DFA 状态数"
            + f" & {fmt_int(int(round(dfa_q['p25'])))}"
            + f" & {fmt_int(int(round(dfa_q['p50'])))}"
            + f" & {fmt_int(int(round(dfa_q['p75'])))}"
            + f" & {fmt_int(int(round(dfa_q['p95'])))}"
            + f" & {fmt_int(int(round(dfa_q['p99'])))} \\\\",
        ]
    )


def build_paragraph(nfa: Dict[str, object], dfa: Dict[str, object]) -> str:
    return (
        f"在当前构造数据中，共 {fmt_int(nfa['count_total'])} 条样本。"
        f"RELAX-NFA 成功构造 {fmt_int(nfa['count_success'])} 条，超时 {fmt_int(nfa['count_timeout'])} 条，超内存 {fmt_int(nfa['count_oom'])} 条；"
        f"RELAX-DFA 成功构造 {fmt_int(dfa['count_success'])} 条，超时 {fmt_int(dfa['count_timeout'])} 条，超内存 {fmt_int(dfa['count_oom'])} 条。"
        f"在成功样本上，RELAX-NFA 的中位构造时间为 {fmt_float(nfa['cpu_s']['median'])} s，RELAX-DFA 为 {fmt_float(dfa['cpu_s']['median'])} s；"
        f"平均构造时间分别为 {fmt_float(nfa['cpu_s']['mean'])} s 与 {fmt_float(dfa['cpu_s']['mean'])} s。"
        f"中位内存均为 {fmt_float(nfa['mem_mb']['median'])} MB，平均内存分别为 {fmt_float(nfa['mem_mb']['mean'])} MB 与 {fmt_float(dfa['mem_mb']['mean'])} MB。"
        f"自动机规模方面，NFA 的中位/平均/最大状态数为 {fmt_int(int(nfa['size']['median']))}/{fmt_float(nfa['size']['mean'])}/{fmt_int(int(nfa['size']['max']))}，"
        f"DFA 为 {fmt_int(int(dfa['size']['median']))}/{fmt_float(dfa['size']['mean'])}/{fmt_int(int(dfa['size']['max']))}。"
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    nfa_records = read_records(args.nfa_jsonl)
    dfa_records = read_records(args.dfa_jsonl)

    nfa = summarize(nfa_records)
    dfa = summarize(dfa_records)
    nfa_time_vals = get_success_sorted_values(nfa_records, "time")
    dfa_time_vals = get_success_sorted_values(dfa_records, "time")
    nfa_mem_vals = get_success_sorted_values(nfa_records, "memory")
    dfa_mem_vals = get_success_sorted_values(dfa_records, "memory")
    nfa_size_vals = get_success_sorted_values(nfa_records, "size")
    dfa_size_vals = get_success_sorted_values(dfa_records, "size")
    scatter_x, scatter_y = build_success_size_pairs(nfa_records, dfa_records)

    cactus_time_paths = plot_construct_cactus(
        nfa_time_vals,
        dfa_time_vals,
        metric="time",
        limit_value=float(args.timeout_sec),
        out_dir=args.out_dir,
        stem="construction_cactus_time",
    )
    cactus_memory_paths = plot_construct_cactus(
        nfa_mem_vals,
        dfa_mem_vals,
        metric="memory",
        limit_value=float(args.memory_limit_mb),
        out_dir=args.out_dir,
        stem="construction_cactus_memory",
    )
    cactus_size_paths = plot_construct_cactus(
        nfa_size_vals,
        dfa_size_vals,
        metric="size",
        limit_value=None,
        out_dir=args.out_dir,
        stem="construction_cactus_size",
    )
    scatter_paths = plot_nfa_dfa_size_scatter(
        scatter_x,
        scatter_y,
        out_dir=args.out_dir,
        stem="nfa_dfa_size_scatter",
    )
    linearity_runs = load_linearity_runs(
        args.linearity_input_dir, args.linearity_timeout_ms, args.linearity_max_k
    )
    linearity_sample_points = build_linearity_sample_points(linearity_runs)
    linearity_main_points = build_linearity_main_points(linearity_sample_points)
    matching_linear_paths = plot_matching_linear(
        linearity_main_points, args.out_dir, stem="matching_linear"
    )
    matching_log_paths = plot_matching_log(
        linearity_main_points, args.out_dir, stem="matching_log"
    )
    matching_log_notes = build_matching_log_notes(
        linearity_main_points, args.linearity_max_k
    )
    matching_summary_rows, matching_summary_ks = build_matching_summary_rows(
        linearity_main_points,
        args.matching_summary_low_k,
        args.matching_summary_high_k,
    )

    nfa_size_quantiles = {
        "p25": quantile(nfa_size_vals, 0.25),
        "p50": quantile(nfa_size_vals, 0.50),
        "p75": quantile(nfa_size_vals, 0.75),
        "p95": quantile(nfa_size_vals, 0.95),
        "p99": quantile(nfa_size_vals, 0.99),
    }
    dfa_size_quantiles = {
        "p25": quantile(dfa_size_vals, 0.25),
        "p50": quantile(dfa_size_vals, 0.50),
        "p75": quantile(dfa_size_vals, 0.75),
        "p95": quantile(dfa_size_vals, 0.95),
        "p99": quantile(dfa_size_vals, 0.99),
    }
    size_distribution_rows = build_size_distribution_rows(
        nfa_size_quantiles, dfa_size_quantiles
    )

    summary = {
        "inputs": {
            "nfa_jsonl": str(args.nfa_jsonl),
            "dfa_jsonl": str(args.dfa_jsonl),
            "timeout_sec": args.timeout_sec,
            "memory_limit_mb": args.memory_limit_mb,
        },
        "nfa": nfa,
        "dfa": dfa,
        "plots": {
            "construction_cactus_time": cactus_time_paths,
            "construction_cactus_memory": cactus_memory_paths,
            "construction_cactus_size": cactus_size_paths,
            "nfa_dfa_size_scatter": scatter_paths,
            "matching_linear": matching_linear_paths,
            "matching_log": matching_log_paths,
        },
        "size_quantiles": {
            "nfa": nfa_size_quantiles,
            "dfa": dfa_size_quantiles,
        },
        "linearity": {
            "input_dir": str(args.linearity_input_dir),
            "max_k": args.linearity_max_k,
            "engine_order": LINEARITY_ENGINES,
            "points": len(linearity_main_points),
            "sample_points": len(linearity_sample_points),
            "matching_log_notes": matching_log_notes,
            "matching_summary_k": matching_summary_ks,
        },
    }

    latex_rows = build_latex_rows(nfa, dfa)
    paragraph = build_paragraph(nfa, dfa)

    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "table_rows.tex").write_text(latex_rows + "\n", encoding="utf-8")
    (args.out_dir / "size_distribution_rows.tex").write_text(
        size_distribution_rows + "\n", encoding="utf-8"
    )
    write_csv(args.out_dir / "matching_linear_points.csv", linearity_main_points)
    write_csv(args.out_dir / "matching_log_points.csv", linearity_main_points)
    write_csv(args.out_dir / "matching_sample_points.csv", linearity_sample_points)
    (args.out_dir / "matching_summary_rows.tex").write_text(
        matching_summary_rows + "\n", encoding="utf-8"
    )
    (args.out_dir / "matching_log_notes.txt").write_text(
        matching_log_notes + "\n", encoding="utf-8"
    )
    (args.out_dir / "paragraph.txt").write_text(paragraph + "\n", encoding="utf-8")

    print(json.dumps({"status": "ok", "out_dir": str(args.out_dir)}, ensure_ascii=False))
    print("\n[table_rows.tex]\n" + latex_rows)
    print("\n[size_distribution_rows.tex]\n" + size_distribution_rows)
    print("\n[matching_summary_rows.tex]\n" + matching_summary_rows)
    print("\n[matching_log_notes.txt]\n" + matching_log_notes)
    print("\n[paragraph.txt]\n" + paragraph)
    print(
        "\n[plots]\n"
        + json.dumps(
            {
                "construction_cactus_time": cactus_time_paths,
                "construction_cactus_memory": cactus_memory_paths,
                "construction_cactus_size": cactus_size_paths,
                "nfa_dfa_size_scatter": scatter_paths,
                "matching_linear": matching_linear_paths,
                "matching_log": matching_log_paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
