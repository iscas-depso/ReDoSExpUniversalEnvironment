import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import sys

TOOLS = [
    "rengar",
    "regexploit",
    "ere",
    "rescue",
    "recheck",
    "revealer",
    "redoshunter",
    # "regexstatic",
    # "regulator",
]


def load_tool_results(directory):
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

    for file_path in tqdm(files, desc="Loading results"):
        filename = os.path.basename(file_path)
        is_expr = "expr" in filename
        tool_name = next(
            (tool for tool in TOOLS if tool in filename),
            "unknown_tool",
        )

        tool_data = {}
        raw_data = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line_content in f:
                line_content = line_content.strip()
                if not line_content:
                    continue
                is_redos = False
                try:
                    data = json.loads(line_content)
                    # 唯一标识符
                    key = (data["file"], data["line"])

                    if is_expr:
                        # 解析 output 字段（它是字符串形式的 JSON）
                        output_json = json.loads(data["output"])
                        is_redos = output_json.get("is_redos", False)
                    else:
                        is_redos = data.get("timeout", False)

                    tool_data[key] = is_redos
                    raw_data[key] = line_content
                except (json.JSONDecodeError, KeyError) as e:
                    pass

        all_results[tool_name] = tool_data
        all_raw_data[tool_name] = raw_data

    for tool_name, tool_data in all_results.items():
        total = len(tool_data)
        redos_count = sum(tool_data.values())
        print(f"{tool_name}: {total}/{redos_count}", file=sys.stderr)

    return all_results, all_raw_data


def process_and_plot(all_results, our_tool="ere"):
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

    df.plot(kind="bar", stacked=True, ax=ax, color=colors, edgecolor="gray", width=0.7)

    # 在柱状图中添加具体数值标签
    for container in ax.containers:
        # 根据百分比和总数反推具体个数，如果数值大于 0 则显示
        labels = [
            (
                f"{int(round(v.get_height() * total_vuln_count / 100))}"
                if v.get_height() > 0
                else ""
            )
            for v in container
        ]
        ax.bar_label(container, labels=labels, label_type="center", fontsize=9)

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
    plt.savefig("comparison_result.pdf")
    print("Plot saved as comparison_result.pdf")
    plt.show()


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
            # 找出一个发现了该漏洞的其他工具，并输出其原始数据
            for tool_name, tool_data in all_results.items():
                if tool_name != our_tool and tool_data.get(key, False):
                    print(all_raw_data[tool_name][key])
                    break


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot comparison results from JSONL files."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to the directory containing JSONL files (default: current directory)",
    )
    parser.add_argument(
        "--tool",
        "-t",
        default="ere",
        help="The name of our tool to compare with others (default: ere)",
    )
    parser.add_argument(
        "--show-missed",
        "-s",
        action="store_true",
        help="Print cases where our tool failed but others succeeded",
    )
    args = parser.parse_args()
    current_dir = args.directory
    results, raw_data = load_tool_results(current_dir)

    if results:
        if args.show_missed:
            print_missed_cases(results, raw_data, our_tool=args.tool)
        else:
            process_and_plot(results, our_tool=args.tool)
    else:
        print("No valid JSONL files found.")


if __name__ == "__main__":
    main()
