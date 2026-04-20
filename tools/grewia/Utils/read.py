import chardet


def unicode_to_u_format(text):
    result = []
    for ch in text:
        code_point = ord(ch)
        # 转换所有字符（包括换行符和 ASCII）
        result.append(f"\\u{{{code_point:04X}}}")
    return ''.join(result)

output_path = "output_u_format.txt"
file_path = "/home/HybridAlgSolver/Output/1/9.txt"

# 先读取部分字节来检测编码
with open(file_path, 'rb') as f:
    raw = f.read(100000)  # 读取前 100000 字节
    result = chardet.detect(raw)
    encoding = result['encoding']
    print(f"Detected encoding: {encoding}")

# 用检测到的编码打开文件
with open(file_path, 'r', encoding=encoding, errors='replace') as f:
    text = f.read()

converted = unicode_to_u_format(text)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(converted)

print(f"转换完成，结果保存为 {output_path}")

print(text[:1000])  # 打印前 1000 个字符