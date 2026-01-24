import json
import os
import argparse


def convert_txt_to_jsonl(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f_in, open(
        output_file, "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            # 去掉行尾的换行符
            pattern = line.rstrip("\n")
            if not pattern:
                continue

            # 构造 JSON 对象并写入文件
            json_record = {"pattern": pattern}
            f_out.write(json.dumps(json_record, ensure_ascii=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description="将 TXT 文件转换为 JSONL 格式")
    parser.add_argument("input", help="输入 TXT 文件的路径")
    parser.add_argument("output", help="输出 JSONL 文件的路径")
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if os.path.exists(input_path):
        print(f"正在转换 {input_path} ...")
        try:
            convert_txt_to_jsonl(input_path, output_path)
            print(f"转换完成！输出文件位于: {output_path}")
        except Exception as e:
            print(f"转换过程中出错: {e}")
    else:
        print(f"错误：找不到输入文件 {input_path}")


if __name__ == "__main__":
    main()
