import json
import glob
import os
import re
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import sys

TOOLS = [
    "ere",
    # "recheck",
    "redoshunter",
    "rengar",
    "rescue",
    "regexploit",
    "revealer",
    # "regexstatic",
    # "regulator",
]


def get_args():
    parser = argparse.ArgumentParser(
        description="Generate Benchmark Visualizations (Cactus Plot / Stacked Bar Chart)."
    )

    # --- 基础参数 ---
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default="./",
        help="[Mode 1/2/3/4] 主数据目录",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="超时时间限制 (s)",
    )

    parser.add_argument(
        "--mem-limit",
        type=float,
        default=10240.0,
        help="内存限制 (MB)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="plot.pdf",
        help="输出路径",
    )

    parser.add_argument(
        "--metric",
        "-m",
        type=str,
        choices=["time", "memory"],
        default="time",
        help="指标: 'time' 或 'memory' (仅影响 Mode 3/4 的判定标准及仙人掌图数值)",
    )

    # --- 绘图类型与工具指定 ---
    parser.add_argument(
        "--plot-type",
        "-p",
        type=str,
        choices=["cactus", "stackbar"],
        default="cactus",
        help="绘图类型: 'cactus' (仙人掌图) 或 'stackbar' (堆叠对比条形图)",
    )

    parser.add_argument(
        "--our-tool",
        "-t",
        type=str,
        default="ere",
        help="[Stackbar Only] 指定'我方工具'的名称，用于与其他工具进行 Pairwise 对比",
    )

    # --- 过滤模式参数 ---
    parser.add_argument(
        "--redos-only",
        "-r",
        action="store_true",
        help="[Mode 2] 仅统计工具报告 ReDoS 的实例",
    )

    parser.add_argument(
        "--verify-dir",
        "-v",
        type=str,
        default=None,
        help="[Mode 3/4] 验证数据目录",
    )

    parser.add_argument(
        "--union-verify",
        "-u",
        action="store_true",
        help="[Mode 4] 开启并集验证模式",
    )

    return parser.parse_args()


# ================= 辅助函数 =================


def parse_cputime(stdout_str):
    if not stdout_str:
        return None
    match = re.search(r"cputime=([\d\.]+)s", stdout_str)
    return float(match.group(1)) if match else None


def parse_memory(stdout_str):
    if not stdout_str:
        return None
    match = re.search(r"memory=(\d+)B", stdout_str)
    return int(match.group(1)) / (1024 * 1024) if match else None


def check_is_redos(output_field):
    if not output_field:
        return False
    try:
        data = json.loads(output_field)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("is_redos") is True:
                    return True
        return False
    except:
        return False


def check_verification_success(record):
    stderr = record.get("stderr", "")
    if stderr and "input is not a valid attack" in stderr:
        return False
    if record.get("timeout", False) is True:
        return True
    stdout = record.get("stdout", "")
    if stdout and (
        "terminationreason=cputime-soft" in stdout
        or "terminationreason=cputime" in stdout
    ):
        return True
    return False


# ================= 验证数据加载 =================


def load_verification_data(verify_dir):
    tool_verification_map = {}
    global_verified_set = set()
    files = [
        f
        for f in glob.glob(os.path.join(verify_dir, "*.json*"))
        if any(t in os.path.basename(f) for t in TOOLS)
    ]

    if not files:
        print(f"[Verify] No files in {verify_dir}", file=sys.stderr)
        return {}, set()

    print(f"[Verify] Loading {len(files)} files...", file=sys.stderr)
    for filepath in files:
        tool_name = next(
            (t for t in TOOLS if t in os.path.basename(filepath)), "unknown"
        )
        if tool_name not in tool_verification_map:
            tool_verification_map[tool_name] = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                        key = (rec.get("file"), rec.get("line"))
                        if check_verification_success(rec):
                            tool_verification_map[tool_name][key] = True
                            global_verified_set.add(key)
                        else:
                            tool_verification_map[tool_name][key] = False
                    except:
                        continue
        except:
            pass
    return tool_verification_map, global_verified_set


# ================= 核心过滤逻辑 (复用) =================


def is_valid_record(record, tool_name, args, tool_verify_map, global_verify_set):
    """
    判断一条记录是否在当前 Mode 下有效 (TP / Solved)
    """
    key = (record.get("file"), record.get("line"))
    tool_claims_redos = check_is_redos(record.get("output", ""))

    # --- Mode 过滤 ---
    keep_record = False
    if not args.redos_only and not args.verify_dir:  # Mode 1
        keep_record = True
    elif args.redos_only and not args.verify_dir:  # Mode 2
        if tool_claims_redos:
            keep_record = True
    elif args.verify_dir and not args.union_verify:  # Mode 3
        if tool_claims_redos:
            if tool_verify_map.get(tool_name, {}).get(key, False):
                keep_record = True
    elif args.verify_dir and args.union_verify:  # Mode 4
        if tool_claims_redos:
            if key in global_verify_set:
                keep_record = True

    if not keep_record:
        return False

    # --- 数值有效性判定 (是否 Solved) ---
    # 只有在限制范围内解决的才算有效记录
    stdout = record.get("stdout", "")
    term_reason = ""
    tm = re.search(r"terminationreason=(\w+)", stdout)
    if tm:
        term_reason = tm.group(1)
    is_timeout_flag = record.get("timeout", False)

    if args.metric == "time":
        is_timed_out = is_timeout_flag or term_reason in ["cputime", "cputime-soft"]
        if is_timed_out:
            return False  # 超时不算解决
        val = parse_cputime(stdout)
        if val is None or val > args.timeout:
            return False
        return True  # 有效且未超时

    elif args.metric == "memory":
        is_oom = term_reason == "memory"
        if is_oom:
            return False  # OOM 不算解决
        val = parse_memory(stdout)
        if val is None or val > args.mem_limit:
            return False
        return True

    return False


# ================= 数据提取 =================


def process_data(args, tool_verify_map, global_verify_set):
    """
    返回:
    1. cactus_data: { tool: [values...] }  -> 用于仙人掌图
    2. solved_sets: { tool: set((file, line)) } -> 用于堆叠图
    """
    files = [
        f
        for f in glob.glob(os.path.join(args.dir, "*.json*"))
        if any(t in os.path.basename(f) for t in TOOLS)
    ]

    cactus_data = {}
    solved_sets = {}

    for filepath in files:
        tool_name = next(
            (t for t in TOOLS if t in os.path.basename(filepath)), "unknown"
        )
        if tool_name not in cactus_data:
            cactus_data[tool_name] = []
        if tool_name not in solved_sets:
            solved_sets[tool_name] = set()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in tqdm(f, desc=f"Reading {tool_name}"):
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                        if is_valid_record(
                            rec, tool_name, args, tool_verify_map, global_verify_set
                        ):
                            # 提取数值用于仙人掌图
                            stdout = rec.get("stdout", "")
                            val = 0
                            if args.metric == "time":
                                val = (
                                    parse_cputime(stdout) or args.timeout
                                )  # 理论上 is_valid 保证了非None，但防万一
                            else:
                                val = parse_memory(stdout) or args.mem_limit

                            cactus_data[tool_name].append(val)

                            # 提取 Key 用于堆叠图
                            key = (rec.get("file"), rec.get("line"))
                            solved_sets[tool_name].add(key)
                    except:
                        continue
        except Exception as e:
            print(f"Error {filepath}: {e}")

    # 排序仙人掌数据
    for t in cactus_data:
        cactus_data[t].sort()

    return cactus_data, solved_sets


# ================= 绘图: 仙人掌图 =================


def plot_cactus(data_dict, output_image, limit_value, metric, mode_desc):
    plt.figure(figsize=(12, 8))
    colors = plt.get_cmap("tab10").colors
    linestyles = ["-", "--", "-.", ":"]
    sorted_tools = sorted(data_dict.keys())
    max_solved = 0

    if metric == "time":
        y_label, title, min_val = "CPU Time (s)", "Cactus Plot of CPU Time", 0.01
    else:
        y_label, title, min_val = (
            "Memory Usage (MB)",
            "Cactus Plot of Memory Usage",
            1.0,
        )

    for idx, tool_name in enumerate(sorted_tools):
        vals = data_dict[tool_name]
        if not vals:
            continue
        # 再次过滤，虽然 process_data 已经过滤了，但双重保险
        valid_vals = [v for v in vals if v < limit_value]
        if not valid_vals:
            continue

        max_solved = max(max_solved, len(valid_vals))
        plt.plot(
            range(1, len(valid_vals) + 1),
            valid_vals,
            label=f"{tool_name} ({len(valid_vals)})",
            color=colors[idx % len(colors)],
            linestyle=linestyles[idx % len(linestyles)],
            linewidth=2,
            alpha=0.8,
        )

    plt.title(f"{title} (Log Scale)\n[{mode_desc}]", fontsize=14)
    plt.xlabel("Number of Solved Instances", fontsize=12)
    plt.ylabel(f"{y_label} - Log Scale", fontsize=12)
    plt.yscale("log")
    plt.ylim(bottom=min_val, top=limit_value * 1.5)
    plt.xlim(left=0, right=max_solved * 1.05 if max_solved > 0 else 10)
    plt.axhline(
        y=limit_value,
        color="r",
        linestyle="--",
        alpha=0.5,
        label=f"Limit ({int(limit_value)})",
    )
    plt.grid(True, which="major", ls="-", alpha=0.4)
    plt.grid(True, which="minor", ls=":", alpha=0.2)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"Saved cactus plot to {output_image}")


# ================= 绘图: 堆叠条形图 =================


def plot_stacked_bar(solved_sets, our_tool_name, output_image, mode_desc):
    if our_tool_name not in solved_sets:
        print(f"Error: Our tool '{our_tool_name}' not found in data.", file=sys.stderr)
        return

    our_set = solved_sets[our_tool_name]
    # 全集：所有工具解决的问题的并集
    universe = set().union(*solved_sets.values())

    # 准备 DataFrame 数据
    # 行：其他工具
    # 列：四种分类的计数

    other_tools = sorted([t for t in solved_sets.keys() if t != our_tool_name])
    if not other_tools:
        print("Error: No other tools to compare against.", file=sys.stderr)
        return

    data = []
    pct_cols = ["Other Tools Found", "Only Other Tool", "Both Found", "Only Ours Found"]

    for other in other_tools:
        other_set = solved_sets[other]

        both = len(our_set.intersection(other_set))
        only_ours = len(our_set - other_set)
        only_other = len(other_set - our_set)

        # "Other Tools Found" = Universe - (Ours U Other)
        # 即：既没被我们发现，也没被当前对比的工具发现，但是被别的工具发现了
        union_pair = our_set.union(other_set)
        others_found = len(universe - union_pair)

        data.append([others_found, only_other, both, only_ours])

    df = pd.DataFrame(data, index=other_tools, columns=[c + "_count" for c in pct_cols])

    # 计算百分比
    df_total = df.sum(axis=1)
    # 防止除以0
    df_total = df_total.replace(0, 1)

    for i, col in enumerate(pct_cols):
        df[col] = (df[f"{col}_count"] / df_total) * 100

    # --- 绘图 ---
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["#eeeeee", "#f8cecc", "#fff2cc", "#dae8fc"]

    # --- 核心改进：视觉补偿逻辑 ---
    vis_df = df[pct_cols].copy()
    MIN_VIS_PCT = 2.0
    for col in pct_cols:
        vis_df[col] = vis_df[col].apply(lambda x: max(x, MIN_VIS_PCT) if x > 0 else 0)

    row_sums = vis_df.sum(axis=1)
    for col in pct_cols:
        vis_df[col] = (vis_df[col] / row_sums) * 100

    vis_df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=colors,
        edgecolor="#444444",
        linewidth=0.5,
        width=0.7,
    )

    # 添加数值标签
    for i, container in enumerate(ax.containers):
        count_col = pct_cols[i] + "_count"
        # 获取对应列的原始计数
        counts = df[count_col].values
        labels = [f"{int(c)}" if c > 0 else "" for c in counts]
        ax.bar_label(
            container,
            labels=labels,
            label_type="center",
            fontsize=9,
            fontweight="medium",
        )

    ax.set_ylabel("Percentage of Total Solved Cases (%)", fontsize=12)
    ax.set_xlabel("Comparison with Other Tools", fontsize=12)
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_title(
        f"Pairwise Comparison: {our_tool_name} vs Others\n[{mode_desc}]", fontsize=14
    )

    # 图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[::-1],
        labels[::-1],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=4,
        frameon=False,
    )

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"Saved stacked bar chart to {output_image}")


def main():
    args = get_args()

    # 1. 确定模式描述
    if not args.verify_dir:
        mode_desc = (
            "Mode 2: ReDoS Claimed" if args.redos_only else "Mode 1: All Instances"
        )
    else:
        mode_desc = "Mode 4: Union TP" if args.union_verify else "Mode 3: Strict TP"

    print(f"Running in {mode_desc}", file=sys.stderr)

    # 2. 加载验证数据
    tool_verify_map = {}
    global_verify_set = set()
    if args.verify_dir:
        tool_verify_map, global_verify_set = load_verification_data(args.verify_dir)

    # 3. 处理数据
    cactus_data, solved_sets = process_data(args, tool_verify_map, global_verify_set)

    if not cactus_data:
        print("No valid data found.", file=sys.stderr)
        return

    # 4. 绘图分支
    limit_val = args.timeout if args.metric == "time" else args.mem_limit

    if args.plot_type == "cactus":
        plot_cactus(cactus_data, args.output, limit_val, args.metric, mode_desc)

    elif args.plot_type == "stackbar":
        if not args.our_tool:
            print("Error: --our-tool is required for stackbar plot.", file=sys.stderr)
            return
        plot_stacked_bar(solved_sets, args.our_tool, args.output, mode_desc)


if __name__ == "__main__":
    main()
