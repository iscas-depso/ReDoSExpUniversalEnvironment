def compare_growth(list0, list1):
    if not list0 or not list1:
        return "两个列表不能为空"
    if list0[0] == 0:
        return "list0 的第一个元素为 0，无法计算增长率"
    for i in range(0, len(list0)):
        value0 = list0[i]
        value1 = list1[i]
        growth = value1 - value0
        growth_rate = growth / value0
        print(f"增长量：{growth}，增长率为：{growth_rate}%")

def compare_sum(list0, list1, list2, list3, list4, list5, list6):
    sum0 = sum(list0)
    sum1 = sum(list1)
    sum2 = sum(list2)
    sum3 = sum(list3)
    sum4 = sum(list4)
    sum5 = sum(list5)
    sum6 = sum(list6)
    print(f"{sum0}, {sum1}, {sum2}, {sum3}, {sum4}, {sum5}, {sum6}")


def unicode_to_u_format(text):
    result = []
    for ch in text:
        code_point = ord(ch)
        # 转换所有字符（包括换行符和 ASCII）
        result.append(f"\\u{{{code_point:04X}}}")
    return ''.join(result)

# 读取输入文件并转换
input_path = "/home/HybridAlgSolver/Output/1/9.txt"
output_path = "output_u_format.txt"

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

converted = unicode_to_u_format(text)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(converted)

print(f"转换完成，结果保存为 {output_path}")

# 示例用法
list0 = [2447, 3562, 3175, 617, 3907, 1307, 3458, 6229, 6012, 3161, 489, 7232, 1918, 5311, 5812, 2831, 867, 465, 2961, 747, 2791, 6667, 6768, 2832, 969, 8023, 6192, 9292]
list1 = [202, 18, 16, 0, 20, 9, 27, 4450, 4660, 1822, 327, 5033, 1139, 3749, 1646, 808, 129, 147, 838, 120, 378, 4571, 4952, 1813, 730, 5100, 1083, 4094]
list2 = [2, 3, 3, 0, 3, 2, 3, 498, 560, 296, 80, 553, 151, 514, 3, 4, 2, 2, 4, 2, 3, 531, 598, 330, 184, 594, 77, 580]
list3 = [3, 3, 0, 0, 3, 0, 3, 275, 311, 140, 10, 728, 203, 302, 5, 13, 14, 2, 25, 10, 13, 292, 327, 146, 15, 682, 202, 318]
list4 = [255, 236, 19, 0, 215, 1, 232, 237, 249, 19, 0, 232, 1, 244, 117, 114, 4, 0, 105, 0, 109, 230, 236, 16, 0, 226, 0, 233]
list5 = [118, 3, 2, 0, 3, 3, 3, 3251, 3180, 662, 144, 3248, 788, 2514, 46, 185, 71, 57, 178, 54, 185, 3734, 3809, 793, 280, 3846, 837, 3122]
list6 = [17, 14, 12, 0, 16, 8, 22, 2427, 2614, 1400, 237, 2735, 1211, 2624, 12, 64, 86, 21, 112, 46, 76, 2442, 2720, 1378, 532, 2722, 1245, 2683]

list8 = [5812, 2831, 2961, 2791]
list9 = [6667, 6768, 8023, 9297]

text = input("Enter text: ")
print(''.join(f"\\u{{{ord(c):x}}}" for c in text))
print(compare_growth(list8, list9))
# print(compare_sum(list0, list1, list2, list3, list4, list5, list6))