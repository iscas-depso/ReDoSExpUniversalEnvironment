#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze NFA/DFA construct benchmark results (fullmatch scope)."
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
        default=Path("expr/results/3_construct/analysis"),
        help="Output directory for CSV/JSON/figures",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=6.0,
        help="Soft timeout baseline in seconds for DFA timeout detection",
    )
    parser.add_argument(
        "--bucket-mode",
        choices=["quantile"],
        default="quantile",
        help="Length bucket strategy (currently only quantile)",
    )
    parser.add_argument(
        "--bucket-count",
        type=int,
        default=10,
        help="Number of length buckets",
    )
    return parser.parse_args()


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON at {path}:{idx}: {exc}") from exc
            rows.append(obj)
    return rows


def parse_cputime(stdout_field):
    if not isinstance(stdout_field, str):
        return None
    m = re.search(r"cputime=([\d\.]+)s", stdout_field)
    if not m:
        return None
    return float(m.group(1))


def is_dfa_soft_timeout(record, timeout_sec):
    if record.get("output") is not None:
        return False
    stdout = record.get("stdout", "")
    if not isinstance(stdout, str):
        return False
    if "terminationreason=cputime-soft" in stdout:
        return True
    if "terminationreason=cputime" in stdout:
        cputime = parse_cputime(stdout)
        if cputime is not None and cputime >= timeout_sec * 0.95:
            return True
    return False


def extract_size(record):
    output = record.get("output")
    if isinstance(output, dict):
        size = output.get("size")
        if isinstance(size, int):
            return size
    return None


def classify_nfa(record):
    size = extract_size(record)
    if size is not None:
        return "success"
    return "other_failure"


def classify_dfa(record, timeout_sec):
    size = extract_size(record)
    if size is not None:
        return "success"
    if is_dfa_soft_timeout(record, timeout_sec):
        return "dfa_soft_timeout"
    return "other_failure"


def key_of(record):
    return (record.get("file"), record.get("line"), record.get("pattern"))


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = (len(sorted_vals) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_fig_dual(fig, out_dir: Path, stem: str):
    pdf = out_dir / f"{stem}.pdf"
    png = out_dir / f"{stem}.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_length_buckets(joined_rows, bucket_count):
    if not joined_rows:
        return []

    rows = sorted(joined_rows, key=lambda x: x["pattern_len_chars"])
    n = len(rows)
    k = max(1, bucket_count)

    buckets = [[] for _ in range(k)]
    for i, row in enumerate(rows):
        bucket_id = min(k - 1, (i * k) // n)
        buckets[bucket_id].append(row)

    out = []
    for bid, bucket in enumerate(buckets):
        if not bucket:
            continue
        lens = sorted(x["pattern_len_chars"] for x in bucket)
        nfas = sorted(x["nfa_size"] for x in bucket)
        dfas = sorted(x["dfa_size"] for x in bucket)
        ratios = sorted(x["size_ratio"] for x in bucket)
        out.append(
            {
                "bucket_id": bid,
                "count": len(bucket),
                "len_min": lens[0],
                "len_max": lens[-1],
                "len_p50": quantile(lens, 0.5),
                "nfa_p50": quantile(nfas, 0.5),
                "nfa_p90": quantile(nfas, 0.9),
                "nfa_p99": quantile(nfas, 0.99),
                "dfa_p50": quantile(dfas, 0.5),
                "dfa_p90": quantile(dfas, 0.9),
                "dfa_p99": quantile(dfas, 0.99),
                "ratio_p50": quantile(ratios, 0.5),
                "ratio_p90": quantile(ratios, 0.9),
            }
        )
    return out


def plot_cdf(joined_rows, out_dir):
    nfa_sizes = sorted(x["nfa_size"] for x in joined_rows)
    dfa_sizes = sorted(x["dfa_size"] for x in joined_rows)

    def cdf_xy(vals):
        n = len(vals)
        xs = vals
        ys = [(i + 1) / n for i in range(n)]
        return xs, ys

    fig, ax = plt.subplots(figsize=(8, 5))
    xn, yn = cdf_xy(nfa_sizes)
    xd, yd = cdf_xy(dfa_sizes)
    ax.plot(xn, yn, label="NFA size", color="#1f77b4")
    ax.plot(xd, yd, label="DFA size", color="#d62728")
    ax.set_xscale("log")
    ax.set_xlabel("Automata size (log scale)")
    ax.set_ylabel("CDF")
    ax.set_title("Construct Size CDF (fullmatch dataset)")
    ax.grid(alpha=0.25)
    ax.legend()
    save_fig_dual(fig, out_dir, "cdf_nfa_dfa_size")


def plot_len_vs_size(joined_rows, out_dir):
    x = [r["pattern_len_chars"] for r in joined_rows]
    y_nfa = [r["nfa_size"] for r in joined_rows]
    y_dfa = [r["dfa_size"] for r in joined_rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y_nfa, s=8, alpha=0.25, label="NFA", color="#1f77b4")
    ax.scatter(x, y_dfa, s=8, alpha=0.25, label="DFA", color="#d62728")
    ax.set_yscale("log")
    ax.set_xlabel("Pattern length (characters)")
    ax.set_ylabel("Automata size (log scale)")
    ax.set_title("Pattern Length vs Size (fullmatch dataset)")
    ax.grid(alpha=0.25)
    ax.legend(markerscale=2)
    save_fig_dual(fig, out_dir, "scatter_len_vs_size")


def plot_nfa_vs_dfa(joined_rows, out_dir):
    xs = [r["nfa_size"] for r in joined_rows]
    ys = [r["dfa_size"] for r in joined_rows]

    lo = min(min(xs), min(ys))
    hi = max(max(xs), max(ys))

    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(xs, ys, s=8, alpha=0.3, color="#2ca02c")
    ax.plot([lo, hi], [lo, hi], linestyle="--", color="#444444", linewidth=1.2, label="y=x")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("NFA size (log scale)")
    ax.set_ylabel("DFA size (log scale)")
    ax.set_title("NFA vs DFA Size (fullmatch dataset)")
    ax.grid(alpha=0.25)
    ax.legend()
    save_fig_dual(fig, out_dir, "scatter_nfa_vs_dfa")


def plot_failure_bar(failure_rows, out_dir):
    order = [
        "dfa_soft_timeout",
        "dfa_other_failure",
        "nfa_other_failure",
        "both_failed",
    ]
    lookup = {r["category"]: r["count"] for r in failure_rows}
    labels = [x for x in order if x in lookup]
    values = [lookup[x] for x in labels]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(labels, values, color=["#ff7f0e", "#d62728", "#1f77b4", "#7f7f7f"][: len(labels)])
    ax.set_ylabel("Count")
    ax.set_title("Failure Breakdown (fullmatch dataset)")
    ax.grid(axis="y", alpha=0.25)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2.0, h, str(int(h)), ha="center", va="bottom", fontsize=9)
    save_fig_dual(fig, out_dir, "bar_failure_breakdown")


def main():
    args = parse_args()

    nfa_rows = read_jsonl(args.nfa_jsonl)
    dfa_rows = read_jsonl(args.dfa_jsonl)

    nfa_map = {key_of(r): r for r in nfa_rows}
    dfa_map = {key_of(r): r for r in dfa_rows}

    common_keys = sorted(set(nfa_map).intersection(dfa_map), key=lambda x: (str(x[0]), x[1]))

    joined_success = []
    dfa_soft_timeout_rows = []

    nfa_success_count = 0
    nfa_other_failure_count = 0
    dfa_success_count = 0
    dfa_soft_timeout_count = 0
    dfa_other_failure_count = 0
    both_failed_count = 0

    for key in common_keys:
        n = nfa_map[key]
        d = dfa_map[key]

        n_status = classify_nfa(n)
        d_status = classify_dfa(d, args.timeout_sec)

        if n_status == "success":
            nfa_success_count += 1
        else:
            nfa_other_failure_count += 1

        if d_status == "success":
            dfa_success_count += 1
        elif d_status == "dfa_soft_timeout":
            dfa_soft_timeout_count += 1
            dfa_soft_timeout_rows.append(
                {
                    "file": d.get("file"),
                    "line": d.get("line"),
                    "pattern": d.get("pattern"),
                    "stdout": d.get("stdout", ""),
                    "stderr": d.get("stderr", ""),
                }
            )
        else:
            dfa_other_failure_count += 1

        n_size = extract_size(n)
        d_size = extract_size(d)

        if isinstance(n_size, int) and isinstance(d_size, int):
            plen = len(d.get("pattern", "")) if isinstance(d.get("pattern"), str) else 0
            joined_success.append(
                {
                    "file": d.get("file"),
                    "line": d.get("line"),
                    "pattern": d.get("pattern"),
                    "pattern_len_chars": plen,
                    "nfa_size": n_size,
                    "dfa_size": d_size,
                    "size_ratio": d_size / n_size if n_size else float("nan"),
                    "size_diff": d_size - n_size,
                }
            )
        elif not isinstance(n_size, int) and not isinstance(d_size, int):
            both_failed_count += 1

    joined_success.sort(key=lambda x: (str(x["file"]), x["line"]))

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        out_dir / "joined_success.csv",
        joined_success,
        [
            "file",
            "line",
            "pattern",
            "pattern_len_chars",
            "nfa_size",
            "dfa_size",
            "size_ratio",
            "size_diff",
        ],
    )

    failure_rows = [
        {"category": "dfa_soft_timeout", "count": dfa_soft_timeout_count},
        {"category": "dfa_other_failure", "count": dfa_other_failure_count},
        {"category": "nfa_other_failure", "count": nfa_other_failure_count},
        {"category": "both_failed", "count": both_failed_count},
    ]
    write_csv(out_dir / "failure_breakdown.csv", failure_rows, ["category", "count"])

    write_csv(
        out_dir / "dfa_soft_timeout.csv",
        dfa_soft_timeout_rows,
        ["file", "line", "pattern", "stdout", "stderr"],
    )

    length_bucket_rows = build_length_buckets(joined_success, args.bucket_count)
    write_csv(
        out_dir / "length_bucket_stats.csv",
        length_bucket_rows,
        [
            "bucket_id",
            "count",
            "len_min",
            "len_max",
            "len_p50",
            "nfa_p50",
            "nfa_p90",
            "nfa_p99",
            "dfa_p50",
            "dfa_p90",
            "dfa_p99",
            "ratio_p50",
            "ratio_p90",
        ],
    )

    summary = {
        "dataset_scope": "fullmatch",
        "inclusion_policy": "main_stats_exclude_dfa_soft_timeout",
        "inputs": {
            "nfa_jsonl": str(args.nfa_jsonl),
            "dfa_jsonl": str(args.dfa_jsonl),
            "timeout_sec": args.timeout_sec,
            "bucket_mode": args.bucket_mode,
            "bucket_count": args.bucket_count,
        },
        "counts": {
            "total_nfa": len(nfa_rows),
            "total_dfa": len(dfa_rows),
            "common_keys": len(common_keys),
            "nfa_success": nfa_success_count,
            "nfa_other_failure": nfa_other_failure_count,
            "dfa_success": dfa_success_count,
            "dfa_soft_timeout": dfa_soft_timeout_count,
            "dfa_other_failure": dfa_other_failure_count,
            "both_success": len(joined_success),
            "both_failed": both_failed_count,
        },
        "rates": {
            "nfa_success_rate": (nfa_success_count / len(nfa_rows)) if nfa_rows else 0.0,
            "dfa_success_rate": (dfa_success_count / len(dfa_rows)) if dfa_rows else 0.0,
            "dfa_soft_timeout_rate": (dfa_soft_timeout_count / len(dfa_rows)) if dfa_rows else 0.0,
        },
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=True, indent=2)

    if joined_success:
        plot_cdf(joined_success, out_dir)
        plot_len_vs_size(joined_success, out_dir)
        plot_nfa_vs_dfa(joined_success, out_dir)
    plot_failure_bar(failure_rows, out_dir)

    print(json.dumps({"status": "ok", "out_dir": str(out_dir), "summary": summary["counts"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
