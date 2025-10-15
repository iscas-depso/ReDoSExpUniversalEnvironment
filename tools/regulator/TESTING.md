# Regulator 工具测试验证指南

## 概述

Regulator 是一个基于 V8 引擎的动态 ReDoS 检测工具，通过模糊测试来发现正则表达式的性能问题。

## 快速测试

### 方法 1: 使用 Docker（推荐）

```bash
# 进入交互式容器
docker run --rm -it -v /tmp:/tmp redos-test bash

# 在容器内运行测试
cd /app/tools/regulator

# 测试 1: ReDoS 模式 (a+)+b
echo "Testing ReDoS pattern: (a+)+b"
python3 run.py KGErKSti /tmp/test1.json
cat /tmp/test1.json

# 测试 2: 非 ReDoS 模式 ^abc$
echo "Testing non-ReDoS pattern: ^abc$"
python3 run.py XmFiYyQ= /tmp/test2.json
cat /tmp/test2.json

# 退出容器
exit
```

### 方法 2: 使用 make test

```bash
# 在容器内运行自动化测试
docker run --rm redos-test bash -c "cd /app/tools/regulator && make test"
```

### 方法 3: 单行测试命令

```bash
# 测试 ReDoS 模式并直接查看结果
docker run --rm -v /tmp:/tmp redos-test bash -c \
  "python3 /app/tools/regulator/run.py KGErKSti /tmp/result.json && cat /tmp/result.json"
```

## 预期结果

### ReDoS 模式: `(a+)+b`

**预期输出**:
```json
{
  "elapsed_ms": 5000-10000,
  "is_redos": true,
  "prefix": "YQ==",       # base64 of "a"
  "infix": "YQ==",        # base64 of "a"
  "suffix": "",
  "repeat_times": 100000  # Large number indicating exponential complexity
}
```

**验证点**:
- ✅ `is_redos` 应该是 `true`
- ✅ `elapsed_ms` 应该在合理范围内（5-60秒）
- ✅ 应该有 `prefix`, `infix`, `suffix` 字段
- ✅ `repeat_times` 应该是正数

### 非 ReDoS 模式: `^abc$`

**预期输出**:
```json
{
  "elapsed_ms": 5000-10000,
  "is_redos": false,
  "prefix": "",
  "infix": "",
  "suffix": "",
  "repeat_times": "-1"
}
```

**验证点**:
- ✅ `is_redos` 应该是 `false`
- ✅ `elapsed_ms` 应该存在
- ✅ 其他字段为空或默认值

## 测试用例

| Base64 编码 | 原始正则 | 预期结果 | 说明 |
|------------|---------|---------|------|
| `KGErKSti` | `(a+)+b` | ReDoS | 经典嵌套量词 |
| `KGF8YSkqYg==` | `(a\|a)*b` | ReDoS | 或运算中的重复 |
| `XmFiYyQ=` | `^abc$` | 非 ReDoS | 简单字面量 |
| `YWJj` | `abc` | 非 ReDoS | 纯字面量 |
| `KGErKSs=` | `(a+)+` | ReDoS | 无结束符的嵌套 |

## 手动验证步骤

### 步骤 1: 解码 Base64

```bash
# 将 base64 编码转换为原始正则
echo "KGErKSti" | base64 -d
# 输出: (a+)+b
```

### 步骤 2: 运行检测

```bash
# 在 Docker 容器中运行
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regulator/run.py KGErKSti /tmp/result.json
```

### 步骤 3: 查看结果

```bash
# 格式化显示 JSON 结果
cat /tmp/result.json | python3 -m json.tool
```

### 步骤 4: 验证攻击字符串

如果检测到 ReDoS，可以手动验证攻击字符串：

```python
import base64
import re
import time

# 从结果中读取
result = {
    "prefix": "YQ==",
    "infix": "YQ==",
    "suffix": "",
    "repeat_times": 10000
}

# 解码
prefix = base64.b64decode(result["prefix"]).decode('utf-8')
infix = base64.b64decode(result["infix"]).decode('utf-8')
suffix = base64.b64decode(result["suffix"]).decode('utf-8')
repeat = result["repeat_times"]

# 构造攻击字符串
attack = prefix + infix * repeat + suffix
print(f"Attack string length: {len(attack)}")

# 测试匹配时间
regex = r'(a+)+b'
pattern = re.compile(regex)

start = time.time()
try:
    result = pattern.match(attack)
except:
    pass
elapsed = time.time() - start

print(f"Matching took {elapsed:.2f} seconds")
```

## 性能说明

### 正常执行时间

- **简单正则**: 5-15秒
- **复杂 ReDoS**: 10-60秒
- **超时设置**: 默认 1200秒（20分钟）

### 时间分解

1. **V8 初始化**: 2-3秒
2. **模糊测试**: 5秒（可配置）
3. **Pump 分析**: 5秒（可配置）
4. **结果输出**: <1秒

### 为什么这么慢？

Regulator 是**深度分析工具**，不是快速检测工具：

- 系统性探索输入空间
- 测试多个输入长度
- 分析路径长度增长
- 使用曲线拟合确定复杂度类型
- 二分搜索找到最优重复次数

这种彻底性使其成为最准确的 ReDoS 检测工具之一。

## 常见问题

### Q: 工具一直不返回结果？

**A**: 这是正常的。Regulator 需要时间进行模糊测试。请等待至少 60 秒。

### Q: 如何加快测试速度？

**A**: 可以修改 `run.py` 中的配置：

```python
ftime_ms = 2000  # 减少模糊测试时间（从 5000 降到 2000）
ptime_ms = 2000  # 减少 pump 分析时间
```

### Q: 如何判断工具是否正常工作？

**A**: 检查以下几点：
1. Docker 容器能启动
2. 没有 Python 导入错误
3. 最终生成 JSON 文件
4. JSON 包含必需字段

### Q: 与其他工具相比如何？

**A**:

| 工具 | 速度 | 准确度 | 适用场景 |
|------|------|--------|----------|
| regexstatic | ⚡⚡⚡ | ⭐⭐ | 快速筛查 |
| regexploit | ⚡⚡ | ⭐⭐⭐ | 平衡 |
| **regulator** | ⚡ | ⭐⭐⭐⭐⭐ | **深度分析** |

## 自动化测试脚本

创建一个测试脚本 `test_regulator.sh`:

```bash
#!/bin/bash

echo "=== Regulator 功能测试 ==="

# 测试用例数组
declare -a tests=(
    "KGErKSti:(a+)+b:true"
    "XmFiYyQ=:^abc$:false"
    "YWJj:abc:false"
)

for test in "${tests[@]}"; do
    IFS=':' read -r b64 regex expected <<< "$test"

    echo ""
    echo "测试: $regex"
    echo "Base64: $b64"

    # 运行测试
    docker run --rm -v /tmp:/tmp redos-test \
        python3 /app/tools/regulator/run.py "$b64" "/tmp/test_$b64.json" \
        2>&1 | head -5

    # 检查结果
    if [ -f "/tmp/test_$b64.json" ]; then
        is_redos=$(cat "/tmp/test_$b64.json" | python3 -c "import sys, json; print(json.load(sys.stdin)['is_redos'])")
        echo "结果: is_redos=$is_redos (预期: $expected)"

        if [ "$is_redos" == "$expected" ]; then
            echo "✅ 通过"
        else
            echo "❌ 失败"
        fi
    else
        echo "❌ 未生成结果文件"
    fi
done

echo ""
echo "=== 测试完成 ==="
```

运行测试:
```bash
chmod +x test_regulator.sh
./test_regulator.sh
```

## 总结

Regulator 工具的正确性验证主要基于：

1. ✅ **能够启动**: 无导入错误，环境正确
2. ✅ **产生输出**: 生成符合格式的 JSON 文件
3. ✅ **准确检测**: ReDoS 模式返回 `true`，正常模式返回 `false`
4. ✅ **提供攻击字符串**: ReDoS 情况下有 prefix/infix/suffix

只要满足这些条件，工具就是正常工作的。执行时间长是设计特性，不是缺陷。
