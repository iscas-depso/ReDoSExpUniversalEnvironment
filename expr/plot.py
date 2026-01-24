import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

TOOLS = [
    "rengar",
    "regexploit",
    "ere",
    "rescue",
    "recheck",
    # "regulator",
    "regexstatic",
    "redoshunter",
]


def load_tool_results(directory):
    """
    扫描目录并加载所有工具的检测结果
    """
    # 查找符合 1_expr_*.json 模式的文件
    files = [
        f
        for f in glob.glob(os.path.join(directory, "1_expr_*.json"))
        if os.path.basename(f).replace("1_expr_", "").replace(".json", "") in TOOLS
    ]

    # 存储结果的嵌套字典: {tool_name: {(file, line): is_redos}}
    all_results = {}

    for file_path in tqdm(files, desc="Loading results"):
        # 提取工具名，例如从 '1_expr_ere.json' 提取 'ere'
        filename = os.path.basename(file_path)
        tool_name = filename.replace("1_expr_", "").replace(".json", "")

        tool_data = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line_content in f:
                if not line_content.strip():
                    continue
                is_redos = False
                try:
                    data = json.loads(line_content)
                    # 唯一标识符
                    key = (data["file"], data["line"])

                    # 解析 output 字段（它是字符串形式的 JSON）
                    output_json = json.loads(data["output"])
                    is_redos = output_json.get("is_redos", False)
                except (json.JSONDecodeError, KeyError) as e:
                    pass
                tool_data[key] = is_redos

        all_results[tool_name] = tool_data

    for tool_name, tool_data in all_results.items():
        total = len(tool_data)
        redos_count = sum(tool_data.values())
        print(f"{tool_name}: {total}/{redos_count}")

    return all_results


def process_and_plot(all_results, our_tool="ere"):
    if our_tool not in all_results:
        print(f"Error: Our tool '{our_tool}' results not found!")
        return

    our_data = all_results[our_tool]
    other_tools = [t for t in all_results.keys() if t != our_tool]

    plot_data = []

    for other in tqdm(other_tools, desc="Processing comparison"):
        other_data = all_results[other]

        # 获取两方都测试过的所有用例的并集
        all_keys = set(our_data.keys()) | set(other_data.keys())

        only_ours = 0
        common = 0
        only_other = 0

        for key in all_keys:
            res_ours = our_data.get(key, False)
            res_other = other_data.get(key, False)

            if res_ours and res_other:
                common += 1
            elif res_ours and not res_other:
                only_ours += 1
            elif not res_ours and res_other:
                only_other += 1

        total = only_ours + common + only_other

        if total > 0:
            # 计算百分比
            plot_data.append(
                {
                    "Tool": other,
                    "Only Other": (only_other / total) * 100,
                    "Common": (common / total) * 100,
                    "Only Ours": (only_ours / total) * 100,
                }
            )

    # 转换为 DataFrame
    df = pd.DataFrame(plot_data)
    # 按 "Only Ours" 比例排序，让图表更有序
    df = df.sort_values(by="Only Ours", ascending=False)
    df.set_index("Tool", inplace=True)

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))

    # 颜色配置（参考论文风格：浅红、浅黄、浅蓝）
    colors = ["#f8cecc", "#fff2cc", "#dae8fc"]

    df.plot(kind="bar", stacked=True, ax=ax, color=colors, edgecolor="gray", width=0.7)

    # 设置样式
    ax.set_ylabel("Percentage of Vulnerabilities Found (%)", fontsize=12)
    ax.set_xlabel("Comparison with Other Tools", fontsize=12)
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # 调整图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[::-1],
        labels[::-1],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=3,
    )

    plt.xticks(rotation=45)
    plt.tight_layout()

    # 保存或显示
    plt.savefig("comparison_result.pdf")
    print("Plot saved as comparison_result.pdf")
    plt.show()


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
    args = parser.parse_args()
    current_dir = args.directory
    results = load_tool_results(current_dir)

    if results:
        process_and_plot(results, our_tool="ere")
    else:
        print("No valid JSONL files found.")


if __name__ == "__main__":
    main()
