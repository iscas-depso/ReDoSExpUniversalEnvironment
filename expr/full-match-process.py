import json

input_file = "./expr/data/csrru.jsonl"  # 原始 jsonl 文件
output_file = "./expr/data/csrru_fullmatch.jsonl"  # 输出文件

with open(input_file, "r", encoding="utf-8") as f_in, open(
    output_file, "w", encoding="utf-8"
) as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        pattern = data.get("pattern", "")
        # 包裹成 ^(?:pattern)$
        data["pattern"] = f"^(?:{pattern})$"
        f_out.write(json.dumps(data, ensure_ascii=True) + "\n")
