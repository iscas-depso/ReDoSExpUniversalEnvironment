import json
import glob
import os
import re
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
import sys

TOOLS = [
    "ere",
    "recheck",
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
        description="Generate Cactus Plots for Time or Memory with Verification Support."
    )

    # --- 基础参数 ---
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default="./",
        help="[Mode 1/2/3/4] 主数据目录：包含工具原始输出的 .json/.jsonl 文件",
    )

    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=600.0,
        help="超时时间限制，单位秒 (默认: 600.0)",
    )

    parser.add_argument(
        "--mem-limit",
        type=float,
        default=10240.0,
        help="内存限制，单位 MB (默认: 10240.0 MB)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="plot.pdf",
        help="输出图片的保存路径",
    )

    parser.add_argument(
        "--metric",
        "-m",
        type=str,
        choices=["time", "memory"],
        default="time",
        help="绘图指标: 'time' 或 'memory'",
    )

    # --- 过滤模式参数 ---

    # Mode 2: 只看工具是否宣称 ReDoS
    parser.add_argument(
        "--redos-only",
        "-r",
        action="store_true",
        help="[Mode 2] 仅统计工具自身报告发现了 ReDoS 的实例 (is_redos=true)",
    )

    # Mode 3 & 4: 验证目录
    parser.add_argument(
        "--verify-dir",
        "-v",
        type=str,
        default=None,
        help="[Mode 3/4] 验证数据目录：包含攻击串验证结果的 .json/.jsonl 文件",
    )

    # Mode 4: 并集验证
    parser.add_argument(
        "--union-verify",
        "-u",
        action="store_true",
        help="[Mode 4] 开启并集验证模式。如果未开启且提供了 verify-dir，则默认为 Mode 3 (严格对应验证)",
    )

    return parser.parse_args()


# ================= 数据解析辅助函数 =================


def parse_cputime(stdout_str):
    if not stdout_str:
        return None
    match = re.search(r"cputime=([\d\.]+)s", stdout_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_memory(stdout_str):
    if not stdout_str:
        return None
    match = re.search(r"memory=(\d+)B", stdout_str)
    if match:
        try:
            bytes_val = int(match.group(1))
            return bytes_val / (1024 * 1024)
        except ValueError:
            return None
    return None


def check_is_redos(output_field):
    """
    解析 dir1 中工具输出的 output 字段，判断工具是否认为有 ReDoS
    """
    if not output_field:
        return False
    try:
        data = json.loads(output_field)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("is_redos") is True:
                    return True
        return False
    except (json.JSONDecodeError, TypeError):
        return False


def check_verification_success(record):
    """
    解析 dir2 中的记录，判断攻击是否真实生效 (TP)
    标准：
    1. stderr 中没有 "input is not a valid attack"
    2. timeout=True 或者 terminationreason=cputime-soft/cputime
    """
    stderr = record.get("stderr", "")
    if stderr and "input is not a valid attack" in stderr:
        return False

    if record.get("timeout", False) is True:
        return True

    stdout = record.get("stdout", "")
    if stdout:
        # 检查 terminationreason
        if "terminationreason=cputime-soft" in stdout:
            return True
        if "terminationreason=cputime" in stdout:
            return True

        # 也可以根据 walltime/cputime 是否超过阈值判断，但通常 benchExec 会写 terminationreason
        # 这里严格按照 benchExec 的标记

    return False


# ================= 验证数据加载逻辑 =================


def load_verification_data(verify_dir):
    """
    预读取验证目录下的所有数据。
    返回:
    1. tool_verification_map: { tool_name: { (file, line): True } }
    2. global_verified_set: Set( (file, line) )
    """
    tool_verification_map = {}
    global_verified_set = set()

    files = [
        f
        for f in glob.glob(os.path.join(verify_dir, "*.json*"))  # 兼容 json 和 jsonl
        if any(tool in os.path.basename(f) for tool in TOOLS)
    ]

    if not files:
        print(
            f"[Verify] Warning: No verification files found in {verify_dir}",
            file=sys.stderr,
        )
        return {}, set()

    print(
        f"[Verify] Loading verification data from {len(files)} files...",
        file=sys.stderr,
    )

    for filepath in files:
        tool_name = next(
            (tool for tool in TOOLS if tool in os.path.basename(filepath)),
            "unknown_tool",
        )

        if tool_name not in tool_verification_map:
            tool_verification_map[tool_name] = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        # 唯一标识符
                        key = (record.get("file"), record.get("line"))

                        # 判断验证是否成功
                        if check_verification_success(record):
                            tool_verification_map[tool_name][key] = True
                            global_verified_set.add(key)
                        else:
                            # 显式记录失败，或者不记录（get时默认None）
                            tool_verification_map[tool_name][key] = False

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[Verify] Error reading {filepath}: {e}", file=sys.stderr)

    print(
        f"[Verify] Loaded. Total unique verified vulnerable cases (Union): {len(global_verified_set)}",
        file=sys.stderr,
    )
    return tool_verification_map, global_verified_set


# ================= 主数据处理逻辑 =================


def process_json_file(filepath, tool_name, args, tool_verify_map, global_verify_set):
    values = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(
                tqdm(f, desc=f"Processing {os.path.basename(filepath)}")
            ):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 唯一标识
                key = (record.get("file"), record.get("line"))

                # --- 核心过滤逻辑 (4种模式) ---

                # 基础信息：工具是否认为自己发现了 ReDoS
                tool_claims_redos = check_is_redos(record.get("output", ""))

                keep_record = False

                # Mode 1: 默认模式 (所有 case 都算)
                if not args.redos_only and not args.verify_dir:
                    keep_record = True

                # Mode 2: 只看工具是否宣称 (无验证)
                elif args.redos_only and not args.verify_dir:
                    if tool_claims_redos:
                        keep_record = True

                # Mode 3: 严格验证 (工具宣称 + 该工具生成的串验证成功)
                elif args.verify_dir and not args.union_verify:
                    if tool_claims_redos:
                        # 查表：当前工具在 verify_dir 中对应条目是否成功
                        # 注意：如果 verify_map 里没这个 key，说明没跑验证或丢失，视为 False
                        is_verified = tool_verify_map.get(tool_name, {}).get(key, False)
                        if is_verified:
                            keep_record = True

                # Mode 4: 并集验证 (工具宣称 + 任意工具生成的串验证成功)
                elif args.verify_dir and args.union_verify:
                    if tool_claims_redos:
                        # 查集合：该 (file, line) 是否在已知漏洞集合中
                        if key in global_verify_set:
                            keep_record = True

                if not keep_record:
                    continue

                # --- 提取数值 (Time / Memory) ---
                stdout = record.get("stdout", "")
                termination_reason = ""
                term_match = re.search(r"terminationreason=(\w+)", stdout)
                if term_match:
                    termination_reason = term_match.group(1)

                is_timeout_flag = record.get("timeout", False)

                if args.metric == "time":
                    current_time = 0.0
                    is_timed_out = is_timeout_flag or termination_reason in [
                        "cputime",
                        "cputime-soft",
                    ]

                    if is_timed_out:
                        current_time = args.timeout
                    else:
                        parsed_time = parse_cputime(stdout)
                        if parsed_time is not None:
                            current_time = parsed_time
                        else:
                            current_time = args.timeout

                    if current_time > args.timeout:
                        current_time = args.timeout

                    values.append(current_time)

                elif args.metric == "memory":
                    current_mem = 0.0
                    is_oom = termination_reason == "memory"

                    if is_oom:
                        current_mem = args.mem_limit
                    else:
                        parsed_mem = parse_memory(stdout)
                        if parsed_mem is not None:
                            current_mem = parsed_mem
                        else:
                            current_mem = args.mem_limit

                    if current_mem > args.mem_limit:
                        current_mem = args.mem_limit

                    values.append(current_mem)

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return []

    values.sort()
    return values


# ================= 绘图逻辑 =================


def plot_cactus_unified(data_dict, output_image, limit_value, metric, mode_desc):
    plt.figure(figsize=(12, 8))
    colors = plt.get_cmap("tab10").colors
    linestyles = ["-", "--", "-.", ":"]
    sorted_tools = sorted(data_dict.keys())
    max_solved = 0

    if metric == "time":
        y_label = "CPU Time (s)"
        limit_label = f"Timeout ({int(limit_value)}s)"
        title = f"Cactus Plot of CPU Time (Log Scale)\n[{mode_desc}]"
        min_val = 0.01
    else:
        y_label = "Memory Usage (MB)"
        limit_label = f"Mem Limit ({int(limit_value)} MB)"
        title = f"Cactus Plot of Memory Usage (Log Scale)\n[{mode_desc}]"
        min_val = 1.0

    for idx, tool_name in enumerate(sorted_tools):
        raw_values = data_dict[tool_name]
        if not raw_values:
            continue

        # 过滤掉达到 Limit 的点 (只显示 Solved)
        valid_values = [v for v in raw_values if v < limit_value]

        if not valid_values:
            continue

        max_solved = max(max_solved, len(valid_values))
        x_axis = range(1, len(valid_values) + 1)
        y_axis = valid_values

        plt.plot(
            x_axis,
            y_axis,
            label=f"{tool_name} ({len(valid_values)})",
            color=colors[idx % len(colors)],
            linestyle=linestyles[idx % len(linestyles)],
            linewidth=2,
            alpha=0.8,
            marker=None,
        )

    plt.title(title, fontsize=14)
    plt.xlabel("Number of Instances", fontsize=12)
    plt.ylabel(f"{y_label} - Log Scale", fontsize=12)

    plt.yscale("log")
    plt.ylim(bottom=min_val, top=limit_value * 1.5)
    plt.xlim(left=0, right=max_solved * 1.05 if max_solved > 0 else 10)

    plt.axhline(
        y=limit_value,
        color="r",
        linestyle="--",
        alpha=0.5,
        label=limit_label,
    )

    plt.grid(True, which="major", ls="-", alpha=0.4, color="gray")
    plt.grid(True, which="minor", ls=":", alpha=0.2, color="gray")
    plt.legend(loc="upper left", fontsize=10, framealpha=0.9)
    plt.tight_layout()

    print(f"Saving plot to {output_image}...", file=sys.stderr)
    plt.savefig(output_image, dpi=300)


def main():
    args = get_args()

    # 1. 确定运行模式描述
    if not args.verify_dir:
        if args.redos_only:
            mode_desc = "Mode 2: ReDoS Claimed Only"
        else:
            mode_desc = "Mode 1: All Instances"
    else:
        if args.union_verify:
            mode_desc = "Mode 4: Union Verification (TP)"
        else:
            mode_desc = "Mode 3: Strict Verification (TP)"

    print(f"Running in {mode_desc}", file=sys.stderr)
    print(f"Metric: {args.metric}", file=sys.stderr)

    # 2. 如果需要验证，先加载验证数据
    tool_verify_map = {}
    global_verify_set = set()

    if args.verify_dir:
        tool_verify_map, global_verify_set = load_verification_data(args.verify_dir)

    # 3. 扫描主目录文件
    files = [
        f
        for f in glob.glob(os.path.join(args.dir, "*.json*"))
        if any(tool in os.path.basename(f) for tool in TOOLS)
    ]

    if not files:
        print(f"No data files found in directory: {args.dir}", file=sys.stderr)
        return

    # 4. 处理数据
    current_limit = args.timeout if args.metric == "time" else args.mem_limit
    all_tools_data = {}

    for filepath in files:
        tool_name = next(
            (tool for tool in TOOLS if tool in os.path.basename(filepath)),
            "unknown_tool",
        )

        values = process_json_file(
            filepath, tool_name, args, tool_verify_map, global_verify_set
        )
        all_tools_data[tool_name] = values

    # 5. 绘图
    if all_tools_data:
        plot_cactus_unified(
            all_tools_data, args.output, current_limit, args.metric, mode_desc
        )
    else:
        print("No valid data extracted.", file=sys.stderr)


if __name__ == "__main__":
    main()
