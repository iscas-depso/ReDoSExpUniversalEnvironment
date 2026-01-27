import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
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


def load_tool_results(
    directory,
    detect_redos=True,
    no_detect_tool=False,
    our_tool="ere",
    ground_truth=False,
    all_vulnerable_keys=None,
):
    """
    扫描目录并加载所有工具的检测结果
    """
    files = [
        f
        for f in glob.glob(os.path.join(directory, "*.json"))
        if any(tool in os.path.basename(f) for tool in TOOLS)
    ]

    # 存储结果的嵌套字典: {tool_name: {(file, line): is_redos}}
    all_results = {}
    # 存储原始行内容的字典: {tool_name: {(file, line): raw_line}}
    all_raw_data = {}
    # 存储报告的字典: {tool_name: {(file, line): is_report}}
    all_report = {}

    for file_path in tqdm(files, desc="Loading results"):
        filename = os.path.basename(file_path)
        is_expr = "expr" in filename
        tool_name = next(
            (tool for tool in TOOLS if tool in filename),
            "unknown_tool",
        )

        tool_data = {}
        tool_report = {}
        raw_data = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line_content in f:
                line_content = line_content.strip()
                if not line_content:
                    continue
                is_redos = False
                is_report = False
                try:
                    data = json.loads(line_content)
                    # 唯一标识符
                    key = (data["file"], data["line"])
                    if detect_redos:
                        if is_expr:
                            # 解析 output 字段（它是字符串形式的 JSON）
                            output_json = json.loads(data["output"])
                            is_redos = any(
                                obj.get("is_redos", False) for obj in output_json
                            )
                        else:
                            is_report = (
                                data.get("stderr", "") != "input is not a valid attack"
                            )
                            if (tool_name == our_tool and no_detect_tool) or (
                                ground_truth
                                and all_vulnerable_keys is not None
                                and key in all_vulnerable_keys
                            ):
                                is_redos = is_report
                            else:
                                is_redos = data.get(
                                    "timeout", False
                                ) or "terminationreason=" in data.get("stdout", "")
                        tool_report[key] = is_report
                        tool_data[key] = is_redos
                    raw_data[key] = line_content
                except (json.JSONDecodeError, KeyError) as e:
                    pass
        all_report[tool_name] = tool_report
        all_results[tool_name] = tool_data
        all_raw_data[tool_name] = raw_data
    if detect_redos:
        for tool_name, tool_data in all_results.items():
            total = len(tool_data)
            redos_count = sum(tool_data.values())
            report_count = sum(all_report[tool_name].values())
            percentage = redos_count / report_count if report_count > 0 else 0
            print(
                f"{tool_name}: {total}/{report_count}/{redos_count} ({percentage:.2%})",
                file=sys.stderr,
            )

    if ground_truth and all_vulnerable_keys is None:
        all_vulnerable_keys = set()
        for tool_name, tool_data in all_results.items():
            for key, is_redos in tool_data.items():
                if is_redos:
                    all_vulnerable_keys.add(key)
        return load_tool_results(
            directory,
            detect_redos,
            no_detect_tool,
            our_tool,
            ground_truth,
            all_vulnerable_keys,
        )

    return all_results, all_raw_data


def process_and_plot(all_results, our_tool="ere", output_file="comparison_result.pdf"):
    if our_tool not in all_results:
        print(f"Error: Our tool '{our_tool}' results not found!")
        return

    # 1. 找出所有工具发现的所有漏洞的并集 (Totals)
    all_vulnerable_keys = set()
    for tool_name, tool_data in all_results.items():
        for key, is_redos in tool_data.items():
            if is_redos:
                all_vulnerable_keys.add(key)

    total_vuln_count = len(all_vulnerable_keys)
    if total_vuln_count == 0:
        print("No vulnerabilities found by any tool.")
        return

    print(f"Total vulnerable keys across all tools: {total_vuln_count}")

    our_data = all_results[our_tool]
    other_tools = [t for t in all_results.keys() if t != our_tool]

    plot_data = []

    for other in tqdm(other_tools, desc="Processing comparison"):
        other_data = all_results[other]

        only_ours = 0
        common = 0
        only_other = 0
        neither = 0

        for key in all_vulnerable_keys:
            res_ours = our_data.get(key, False)
            res_other = other_data.get(key, False)

            if res_ours and res_other:
                common += 1
            elif res_ours and not res_other:
                only_ours += 1
            elif not res_ours and res_other:
                only_other += 1
            else:
                neither += 1

        # 录入数据，注意顺序对应颜色
        plot_data.append(
            {
                "Tool": other,
                "Other Tools Found": (neither / total_vuln_count) * 100,
                "Only Other Tool": (only_other / total_vuln_count) * 100,
                "Both Found": (common / total_vuln_count) * 100,
                "Only Ours Found": (only_ours / total_vuln_count) * 100,
                "Other Tools Found_count": neither,
                "Only Other Tool_count": only_other,
                "Both Found_count": common,
                "Only Ours Found_count": only_ours,
            }
        )

    # 转换为 DataFrame
    df = pd.DataFrame(plot_data)
    # 按 "Only Ours Found" 比例排序
    df = df.sort_values(by="Only Ours Found", ascending=False)
    df.set_index("Tool", inplace=True)

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))

    # 颜色配置：
    # 蓝色 (#dae8fc) - Only Ours
    # 黄色 (#fff2cc) - Common
    # 红色 (#f8cecc) - Only Other
    # 浅灰色 (#eeeeee) - Neither (Other Tools Found)
    colors = ["#eeeeee", "#f8cecc", "#fff2cc", "#dae8fc"]
    pct_cols = ["Other Tools Found", "Only Other Tool", "Both Found", "Only Ours Found"]

    # --- 核心改进：视觉补偿逻辑 ---
    # 创建一个用于绘图的临时 DataFrame，确保极小值也有最小展示高度
    vis_df = df[pct_cols].copy()
    MIN_VIS_PCT = 2.0  # 定义最小视觉占比 (百分比)
    for col in pct_cols:
        # 只有原本 > 0 的项才进行补偿，0 依然保持为 0
        vis_df[col] = vis_df[col].apply(lambda x: max(x, MIN_VIS_PCT) if x > 0 else 0)

    # 重新归一化到 100%，以保证堆叠高度一致，但比例已经向小值倾斜了
    row_sums = vis_df.sum(axis=1)
    for col in pct_cols:
        vis_df[col] = (vis_df[col] / row_sums) * 100

    # 使用视觉补偿后的数据绘图，并加强边框对比
    vis_df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=colors,
        edgecolor="#444444",
        linewidth=0.5,
        width=0.7,
    )

    # 在柱状图中添加具体数值标签
    for i, container in enumerate(ax.containers):
        # 使用预先保存的具体个数，如果数值大于 0 则显示
        # 注意：这里依然使用原始 df 中的计数列，确保数据的真实准确
        count_col = pct_cols[i] + "_count"
        labels = [f"{int(count)}" if count > 0 else "" for count in df[count_col]]
        ax.bar_label(
            container,
            labels=labels,
            label_type="center",
            fontsize=9,
            fontweight="medium",
        )

    # 设置样式
    ax.set_ylabel("Percentage of Total Vulnerabilities (%)", fontsize=12)
    ax.set_xlabel("Comparison with Other Tools", fontsize=12)
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # 调整图例 (从上到下对应 stack 顺序)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[::-1],
        labels[::-1],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=4,
    )

    plt.xticks(rotation=45)
    plt.tight_layout()

    # 保存或显示
    plt.savefig(output_file)
    print(f"Plot saved as {output_file}")


def print_missed_cases(all_results, all_raw_data, our_tool="ere"):
    """
    输出所有我们的工具没有发现，但其他工具发现了的数据
    """
    if our_tool not in all_results:
        print(f"Error: Our tool '{our_tool}' results not found!")
        return

    our_data = all_results[our_tool]

    # 1. 找出所有工具发现的所有漏洞的并集
    all_vulnerable_keys = set()
    for tool_name, tool_data in all_results.items():
        for key, is_redos in tool_data.items():
            if is_redos:
                all_vulnerable_keys.add(key)

    # 2. 检查哪些是我们的工具漏掉的
    for key in sorted(all_vulnerable_keys):
        res_ours = our_data.get(key, False)
        if not res_ours:
            tool_names = []
            raw_data = None
            # 找出一个发现了该漏洞的其他工具，并输出其原始数据
            # 按照TOOLS的顺序输出
            for tool_name in TOOLS:
                if tool_name == our_tool:
                    continue
                if tool_name not in all_results:
                    continue
                tool_data = all_results[tool_name]
                if tool_data.get(key, False):
                    if raw_data is None:
                        raw_data = json.loads(all_raw_data[tool_name][key])
                    tool_names.append(tool_name)

            if raw_data is not None:
                raw_data = {
                    "tools": tool_names,
                    **raw_data,
                }
                print(json.dumps(raw_data, ensure_ascii=True))


def print_missed_ours(all_results, all_raw_data, our_tool="ere"):
    """
    输出所有我们的工具没有发现，但其他工具发现了的数据
    """
    if our_tool not in all_results:
        print(f"Error: Our tool '{our_tool}' results not found!")
        return

    our_data = all_results[our_tool]

    # 1. 找出所有工具发现的所有漏洞的并集
    all_vulnerable_keys = set()
    for tool_name, tool_data in all_results.items():
        for key, is_redos in tool_data.items():
            if is_redos:
                all_vulnerable_keys.add(key)

    # 2. 检查哪些是我们的工具漏掉的
    for key in sorted(all_vulnerable_keys):
        if our_data.get(key, False):
            continue
        print(all_raw_data[our_tool][key])


def print_only_ours(all_results, all_raw_data, our_tool="ere"):
    """
    输出所有我们的工具发现的数据
    """
    if our_tool not in all_results:
        print(f"Error: Our tool '{our_tool}' results not found!")
        return

    # 1. 找出所有其他工具发现的所有漏洞的并集
    other_vulnerable_keys = set()
    our_vulnerable_keys = set()
    for tool_name, tool_data in all_results.items():
        for key, is_redos in tool_data.items():
            if is_redos:
                if tool_name == our_tool:
                    our_vulnerable_keys.add(key)
                else:
                    other_vulnerable_keys.add(key)

    # 2. 检查哪些是只有我们的工具发现的
    only_ours = our_vulnerable_keys - other_vulnerable_keys
    for key in sorted(only_ours):
        print(all_raw_data[our_tool][key])


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot comparison results from JSONL files."
    )
    parser.add_argument(
        "directory",
        help="Path to the directory containing JSONL files",
    )
    parser.add_argument(
        "--tool",
        "-t",
        default="ere",
        help="Name of our tool (default: ere)",
    )

    parser.add_argument(
        "--show-missed",
        "-m",
        action="store_true",
        help="Show cases missed by our tool but detected by others",
    )

    parser.add_argument(
        "--show-missed-ours",
        "-M",
        action="store_true",
        help="Show all cases our tool failed to detect",
    )

    parser.add_argument(
        "--show-only-ours",
        "-o",
        action="store_true",
        help="Show only cases our tool successfully detected",
    )

    parser.add_argument(
        "--disable-detect",
        "-d",
        action="store_true",
        help="Disable detection for our tool",
    )

    parser.add_argument(
        "--use-ground-truth",
        "-g",
        action="store_true",
        help="Evaluate tools using ground truth",
    )

    parser.add_argument(
        "--output-file",
        "-f",
        default="comparison_result.pdf",
        help="Output file path for the plot (default: comparison_result.pdf)",
    )

    args = parser.parse_args()
    current_dir = args.directory
    results, raw_data = load_tool_results(
        current_dir,
        no_detect_tool=args.disable_detect,
        our_tool=args.tool,
        ground_truth=args.use_ground_truth,
    )

    if results:
        if args.show_missed:
            print_missed_cases(results, raw_data, our_tool=args.tool)
        elif args.show_missed_ours:
            _, nredos_raw_data = load_tool_results(
                current_dir, detect_redos=False, our_tool=args.tool
            )
            print_missed_ours(results, nredos_raw_data, our_tool=args.tool)
        elif args.show_only_ours:
            print_only_ours(results, raw_data, our_tool=args.tool)
        else:
            process_and_plot(results, our_tool=args.tool, output_file=args.output_file)
    else:
        print("No valid JSONL files found.")


if __name__ == "__main__":
    main()
