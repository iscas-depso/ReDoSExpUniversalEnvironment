#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ENGINE_ORDER = ["ere", "ere_dfa", "python", "java11", "nodejs14"]
ENGINE_COLORS = {
    "ere": "#1f77b4",
    "ere_dfa": "#9467bd",
    "python": "#2ca02c",
    "java11": "#d62728",
    "nodejs14": "#ff7f0e",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot linearity benchmark results from JSONL outputs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("./expr/results/2_linearity"),
        help="Directory containing <engine>.jsonl and samples_manifest.jsonl",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("./expr/results/2_linearity/figures"),
        help="Output directory for figures and summaries",
    )
    parser.add_argument(
        "--engines",
        nargs="+",
        default=ENGINE_ORDER,
        help="Engine file names (without .jsonl)",
    )
    parser.add_argument(
        "--linear-x",
        action="store_true",
        help="Use linear x-axis (default is log scale)",
    )
    parser.add_argument(
        "--log-y",
        action="store_true",
        help="Use log scale on y-axis for time plots",
    )
    parser.add_argument(
        "--timeout-ms",
        type=float,
        default=5000.0,
        help="Fallback timeout time in ms for timeout-like records when walltime is missing",
    )
    parser.add_argument(
        "--max-k",
        type=int,
        default=None,
        help="Only plot and summarize points with k <= max_k",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Use dual-panel (detail + full range) layout. "
             "Default is single panel.",
    )
    parser.add_argument(
        "--detail-k",
        type=int,
        default=None,
        help="Upper bound of k for the left (detail) panel (only used with --split). "
             "If omitted, auto-select ~10%% of max k.",
    )
    return parser.parse_args()


# ── helpers ──────────────────────────────────────────────────────────

def quantile(values, q):
    xs = sorted(values)
    if not xs:
        return float("nan")
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs[lo])
    frac = pos - lo
    return float(xs[lo] * (1.0 - frac) + xs[hi] * frac)


def median(values):
    return quantile(values, 0.5)


def parse_time_ms(output_field):
    if not isinstance(output_field, str):
        return None
    try:
        payload = json.loads(output_field)
    except json.JSONDecodeError:
        return None
    t = payload.get("time")
    if isinstance(t, (int, float)):
        return float(t)
    return None


def parse_walltime_ms(stdout_field):
    if not isinstance(stdout_field, str):
        return None
    m = re.search(r"walltime=([\d\.]+)s", stdout_field)
    if not m:
        return None
    return float(m.group(1)) * 1000.0


def is_timeout_like(record):
    if record.get("timeout", False) is True:
        return True
    stdout = record.get("stdout", "")
    if not isinstance(stdout, str):
        return False
    return (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    )


# ── data loading ─────────────────────────────────────────────────────

def read_engine_runs(path, engine, timeout_ms):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            warmup = obj.get("warmup")
            if warmup is True:
                continue

            sample_id = obj.get("sample_id")
            input_bytes = obj.get("input_bytes")
            k = obj.get("k")
            run_id = obj.get("run_id")
            if not (
                isinstance(sample_id, str)
                and isinstance(input_bytes, int)
                and isinstance(k, int)
            ):
                continue

            timed_out = is_timeout_like(obj)
            time_ms = parse_time_ms(obj.get("output"))
            if time_ms is None and timed_out:
                time_ms = parse_walltime_ms(obj.get("stdout", ""))
                if time_ms is None:
                    time_ms = timeout_ms
            if time_ms is None:
                continue

            rows.append(
                {
                    "engine": engine,
                    "sample_id": sample_id,
                    "input_bytes": input_bytes,
                    "k": k,
                    "run_id": run_id,
                    "time_ms": time_ms,
                    "timed_out": timed_out,
                }
            )
    return rows


# ── aggregation ──────────────────────────────────────────────────────

def build_sample_point_summary(runs):
    grouped = defaultdict(list)
    for r in runs:
        grouped[(r["engine"], r["sample_id"], r["k"])].append(r)

    out = []
    for (engine, sample_id, k), rows in grouped.items():
        times = [x["time_ms"] for x in rows]
        bytes_vals = [x["input_bytes"] for x in rows]
        timeout_count = sum(1 for x in rows if x["timed_out"])
        out.append(
            {
                "engine": engine,
                "sample_id": sample_id,
                "k": k,
                "input_bytes_median": int(round(median(bytes_vals))),
                "n_runs": len(times),
                "timed_out_count": timeout_count,
                "timeout_like_rate": timeout_count / len(times) if times else 0.0,
                "time_median_ms": median(times),
                "time_q1_ms": quantile(times, 0.25),
                "time_q3_ms": quantile(times, 0.75),
            }
        )
    out.sort(key=lambda x: (x["engine"], x["sample_id"], x["k"]))
    return out


def build_main_curve_points(sample_points):
    grouped = defaultdict(list)
    for r in sample_points:
        grouped[(r["engine"], r["k"])].append(r)

    out = []
    for (engine, k), rows in grouped.items():
        vals = [x["time_median_ms"] for x in rows]
        bytes_vals = [x["input_bytes_median"] for x in rows]
        timed_out_count = sum(x["timed_out_count"] for x in rows)
        total_count = sum(x["n_runs"] for x in rows)
        out.append(
            {
                "engine": engine,
                "k": k,
                "input_bytes_median": int(round(median(bytes_vals))),
                "n_samples": len(vals),
                "timed_out_count": timed_out_count,
                "total_count": total_count,
                "timeout_like_rate": (
                    timed_out_count / total_count if total_count else 0.0
                ),
                "median_ms": median(vals),
                "q1_ms": quantile(vals, 0.25),
                "q3_ms": quantile(vals, 0.75),
            }
        )
    out.sort(key=lambda x: (x["engine"], x["k"]))
    return out


def build_slope_summary(sample_points):
    per = defaultdict(list)
    for r in sample_points:
        per[(r["engine"], r["sample_id"])].append(r)

    out = []
    for (engine, sample_id), rows in per.items():
        rows = sorted(rows, key=lambda x: x["k"])
        slopes = []
        for i in range(1, len(rows)):
            dx = rows[i]["k"] - rows[i - 1]["k"]
            if dx <= 0:
                continue
            dy = rows[i]["time_median_ms"] - rows[i - 1]["time_median_ms"]
            slopes.append(dy / dx)
        if not slopes:
            continue
        out.append(
            {
                "engine": engine,
                "sample_id": sample_id,
                "slope_median": median(slopes),
                "slope_q1": quantile(slopes, 0.25),
                "slope_q3": quantile(slopes, 0.75),
            }
        )
    out.sort(key=lambda x: (x["engine"], x["sample_id"]))
    return out


def build_max_common_summary(sample_points, engines):
    per_sample = defaultdict(lambda: defaultdict(dict))
    for r in sample_points:
        per_sample[r["sample_id"]][r["engine"]][r["k"]] = r["time_median_ms"]

    out = []
    for sample_id, engine_map in per_sample.items():
        if not all(e in engine_map for e in engines):
            continue
        common_ks = set(engine_map[engines[0]].keys())
        for e in engines[1:]:
            common_ks &= set(engine_map[e].keys())
        if not common_ks:
            continue
        max_k = max(common_ks)
        for e in engines:
            out.append(
                {
                    "sample_id": sample_id,
                    "engine": e,
                    "k": max_k,
                    "time_median_ms": engine_map[e][max_k],
                }
            )
    out.sort(key=lambda x: (x["sample_id"], x["engine"]))
    return out


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── auto-detect detail_k ─────────────────────────────────────────────

def _auto_detail_k(main_points):
    """Pick a split point ≈ 10 % of max k, snapped to the nearest actual k."""
    all_ks = sorted(set(r["k"] for r in main_points))
    if not all_ks:
        return 5000
    max_k = all_ks[-1]
    target = max_k * 0.10
    return min(all_ks, key=lambda v: abs(v - target))


# ── plotting (dual-panel) ───────────────────────────────────────────

def _draw_engine_curves(ax, by_engine, engines, k_max=None):
    """Draw median lines + IQR fill for each engine on *ax*.
    If *k_max* is given, only points with k <= k_max are drawn.
    """
    for e in engines:
        rows = sorted(by_engine.get(e, []), key=lambda x: x["k"])
        if not rows:
            continue
        if k_max is not None:
            rows = [r for r in rows if r["k"] <= k_max]
        if not rows:
            continue
        x = [r["k"] for r in rows]
        y = [r["median_ms"] for r in rows]
        y1 = [r["q1_ms"] for r in rows]
        y3 = [r["q3_ms"] for r in rows]
        c = ENGINE_COLORS.get(e, None)
        ax.plot(x, y, marker="o", linewidth=2, label=e, color=c)
        ax.fill_between(x, y1, y3, alpha=0.20, color=c)


def plot_main_curve(main_points, engines, out_path, linear_x, log_y,
                    split=False, detail_k=None):
    by_engine = defaultdict(list)
    for r in main_points:
        by_engine[r["engine"]].append(r)

    all_ks = sorted(set(r["k"] for r in main_points))
    max_k = all_ks[-1] if all_ks else 50000

    if split:
        # ── dual-panel ──────────────────────────────────────────────
        if detail_k is None:
            detail_k = _auto_detail_k(main_points)

        fig, (ax_detail, ax_full) = plt.subplots(
            1, 2,
            figsize=(16, 6),
            sharey=True,
            gridspec_kw={"width_ratios": [1, 1.3]},
        )

        _draw_engine_curves(ax_detail, by_engine, engines, k_max=detail_k)
        if linear_x:
            ax_detail.set_xlim(left=-detail_k * 0.03, right=detail_k * 1.06)
        else:
            ax_detail.set_xscale("log")
        if log_y:
            ax_detail.set_yscale("log")
        ax_detail.set_xlabel("Infix repeat times (k)")
        ax_detail.set_ylabel("Time (ms)")
        ax_detail.set_title(f"Detail  (k ≤ {detail_k})")
        ax_detail.grid(alpha=0.25)

        _draw_engine_curves(ax_full, by_engine, engines, k_max=None)
        if linear_x:
            ax_full.set_xlim(left=-max_k * 0.02, right=max_k * 1.04)
        else:
            ax_full.set_xscale("log")
        if log_y:
            ax_full.set_yscale("log")
        ax_full.set_xlabel("Infix repeat times (k)")
        ax_full.set_title("Full Range")
        ax_full.grid(alpha=0.25)
        ax_full.legend(loc="best")

        fig.suptitle(
            "Linearity Main Curve (Median with IQR)"
            + (" [log-y]" if log_y else ""),
            fontsize=14,
        )
    else:
        # ── single panel (original) ────────────────────────────────
        fig, ax = plt.subplots(figsize=(9, 6))
        _draw_engine_curves(ax, by_engine, engines, k_max=None)

        if not linear_x:
            ax.set_xscale("log")
        if log_y:
            ax.set_yscale("log")
        ax.set_xlabel("Infix repeat times (k)")
        ax.set_ylabel("Time (ms)")
        ax.set_title(
            "Linearity Main Curve (Median with IQR)"
            + (" [log-y]" if log_y else "")
        )
        ax.grid(alpha=0.25)
        ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_timeout_rate(main_points, engines, out_path, linear_x,
                      split=False, detail_k=None):
    by_engine = defaultdict(list)
    for r in main_points:
        by_engine[r["engine"]].append(r)

    all_ks = sorted(set(r["k"] for r in main_points))
    max_k = all_ks[-1] if all_ks else 50000

    if split:
        if detail_k is None:
            detail_k = _auto_detail_k(main_points)

        fig, (ax_detail, ax_full) = plt.subplots(
            1, 2,
            figsize=(16, 6),
            sharey=True,
            gridspec_kw={"width_ratios": [1, 1.3]},
        )
        axes_info = [
            (ax_detail, detail_k, f"Detail  (k ≤ {detail_k})"),
            (ax_full, None, "Full Range"),
        ]
    else:
        fig, ax = plt.subplots(figsize=(9, 6))
        axes_info = [(ax, None, "Timeout-like Rate vs k")]

    for ax, k_max, subtitle in axes_info:
        for e in engines:
            rows = sorted(by_engine.get(e, []), key=lambda x: x["k"])
            if not rows:
                continue
            if k_max is not None:
                rows = [r for r in rows if r["k"] <= k_max]
            if not rows:
                continue
            x = [r["k"] for r in rows]
            y = [r["timeout_like_rate"] for r in rows]
            c = ENGINE_COLORS.get(e, None)
            ax.plot(x, y, marker="o", linewidth=2, label=e, color=c)

        if not linear_x:
            ax.set_xscale("log")
        ax.set_ylim(0.0, 1.05)
        ax.set_xlabel("Infix repeat times (k)")
        ax.set_title(subtitle)
        ax.grid(alpha=0.25)

    if split:
        if linear_x:
            ax_detail.set_xlim(left=-detail_k * 0.03, right=detail_k * 1.06)
            ax_full.set_xlim(left=-max_k * 0.02, right=max_k * 1.04)
        ax_detail.set_ylabel("Timeout-like rate")
        ax_full.legend(loc="best")
        fig.suptitle("Timeout-like Rate vs k", fontsize=14)
    else:
        ax.set_ylabel("Timeout-like rate")
        ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


# ── box plots (unchanged) ───────────────────────────────────────────

def plot_box(values_by_engine, engines, out_path, title, ylabel):
    data = []
    labels = []
    colors = []
    for e in engines:
        vals = values_by_engine.get(e, [])
        if not vals:
            continue
        data.append(vals)
        labels.append(e)
        colors.append(ENGINE_COLORS.get(e, "#999999"))
    if not data:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    b = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=True)
    for patch, color in zip(b["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


# ── main ─────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    in_dir = args.input_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    engines = list(args.engines)
    runs = []
    for e in engines:
        p = in_dir / f"{e}.jsonl"
        if not p.exists():
            print(f"[WARN] missing file: {p}", file=sys.stderr)
            continue
        runs.extend(read_engine_runs(p, e, args.timeout_ms))

    if not runs:
        raise RuntimeError("No valid non-warmup run records loaded.")

    if args.max_k is not None:
        runs = [r for r in runs if r["k"] <= args.max_k]
        if not runs:
            raise RuntimeError(
                f"No valid records remain after applying k <= {args.max_k}."
            )

    sample_points = build_sample_point_summary(runs)
    main_points = build_main_curve_points(sample_points)
    slope_summary = build_slope_summary(sample_points)
    max_common = build_max_common_summary(sample_points, engines)

    write_csv(out_dir / "sample_point_summary.csv", sample_points)
    write_csv(out_dir / "main_curve_points.csv", main_points)
    write_csv(out_dir / "slope_summary.csv", slope_summary)
    write_csv(out_dir / "max_common_summary.csv", max_common)

    detail_k = args.detail_k  # None means auto

    plot_main_curve(
        main_points,
        engines,
        out_dir / "main_curve.png",
        args.linear_x,
        args.log_y,
        split=args.split,
        detail_k=args.detail_k,
    )
    plot_timeout_rate(
        main_points,
        engines,
        out_dir / "timeout_rate_curve.png",
        args.linear_x,
        split=args.split,
        detail_k=args.detail_k,
    )

    slope_by_engine = defaultdict(list)
    for r in slope_summary:
        slope_by_engine[r["engine"]].append(r["slope_median"])
    plot_box(
        slope_by_engine,
        engines,
        out_dir / "supplement_a_slope_box.png",
        "Supplement A: Per-sample slope distribution",
        "Delta time / Delta k (ms per repeat)",
    )

    max_by_engine = defaultdict(list)
    for r in max_common:
        max_by_engine[r["engine"]].append(r["time_median_ms"])
    plot_box(
        max_by_engine,
        engines,
        out_dir / "supplement_b_max_common_box.png",
        "Supplement B: Max common k",
        "Time (ms)",
    )

    summary = {
        "records_nonwarmup": len(runs),
        "engines": engines,
        "timeout_ms_fallback": args.timeout_ms,
        "n_samples": len({r["sample_id"] for r in runs}),
        "n_sample_points": len(sample_points),
        "n_main_curve_points": len(main_points),
        "n_slope_samples": len(slope_summary),
        "n_max_common_points": len(max_common),
    }
    (out_dir / "plot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8"
    )

    print(f"Wrote plots and summaries to {out_dir}")


if __name__ == "__main__":
    main()
