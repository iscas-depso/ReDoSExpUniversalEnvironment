#!/usr/bin/env python3
import sys


def evaluate(n, detected, true_positive):
    fp = detected - true_positive

    precision = true_positive / detected if detected != 0 else 0
    fp_rate = fp / detected if detected != 0 else 0
    density = detected / n if n != 0 else 0
    true_density = true_positive / n if n != 0 else 0

    print(f"数据组数 (N): {n}")
    print(f"检测漏洞数 (D): {detected}")
    print(f"真实漏洞数 (T): {true_positive}")
    print("-" * 40)
    print(f"准确率 Precision        : {precision:.2%}")
    print(f"误报数 False Positives : {fp}")
    print(f"误报率 FP Rate         : {fp_rate:.2%}")
    print(f"检测漏洞密度           : {density:.4%}")
    print(f"真实漏洞密度           : {true_density:.4%}")


def main():
    if len(sys.argv) != 4:
        print("用法: python eval.py <N> <D> <T>")
        print("示例: python eval.py 49023 5818 5415")
        sys.exit(1)

    try:
        N = int(sys.argv[1])
        D = int(sys.argv[2])
        T = int(sys.argv[3])
    except ValueError:
        print("请输入有效的整数！")
        sys.exit(1)

    evaluate(N, D, T)


if __name__ == "__main__":
    main()
