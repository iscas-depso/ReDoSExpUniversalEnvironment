# ReDoS测试环境 - 重构版

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>
## 中文文档

### 项目简介

这是一个**优化重构后的ReDoS（Regular Expression Denial of Service）测试环境**，用于检测正则表达式的拒绝服务漏洞。

### 快速开始

```bash
# 1. 构建Docker镜像（5-10分钟）
docker build --rm -t redos-test .

# 2. 运行快速验证
bash quick_verify.sh

# 3. 测试单个正则表达式
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json

# 4. 查看结果
cat /tmp/test.json
```

### 核心特性

- **6个ReDoS检测工具**：rescue, regexstatic, regexploit, rengar, redoshunter, regulator
- **19个正则引擎**：Python, C (PCRE2), C++, Java 8/11, Node.js 14/21, C#, Perl, PHP, Ruby, Rust, Go, RE2, Hyperscan等
- **容器化部署**：所有组件预编译，快速部署
- **资源优化**：构建时间缩短90%，内存需求降低95%

### 文档

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 完整的部署文档（系统要求、详细步骤、故障排除）
- **[CLAUDE.md](CLAUDE.md)** - 开发者指南
- **quick_verify.sh** - 快速验证脚本

### 系统要求

- **操作系统**：Ubuntu 20.04/22.04（推荐）或其他Linux发行版
- **Docker**：20.10或更高版本
- **硬件**：4核CPU，8GB内存，20GB磁盘空间（最低配置）

### 工具对比

| 工具 | 类型 | 速度 | 准确度 | 适用场景 |
|------|------|------|--------|---------|
| regexploit | 静态分析 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 快速筛查 |
| regexstatic | 静态分析 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 准确检测 |
| rescue | 混合分析 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 平衡性能和准确度 |
| rengar | 符号执行 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高准确度需求 |
| redoshunter | 动态测试 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 资源受限环境 |
| regulator | 模糊测试 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 全面深度分析 |

### 使用示例

#### 检测单个正则表达式

```bash
# 准备正则表达式（base64编码）
REGEX="(a+)+"
REGEX_B64=$(echo -n "$REGEX" | base64)

# 使用regexploit检测（最快）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py $REGEX_B64 /tmp/result.json

# 查看结果
cat /tmp/result.json
```

#### 验证攻击字符串

```bash
# 创建测试文本
echo "aaaaaaaaaaaaaaaaaaaaaaaaaab" > /tmp/input.txt

# 使用Python引擎测试
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/python/bin/benchmark $REGEX_B64 /tmp/input.txt 0
```

### 项目结构

```
ReDoSExpUniversalEnvironment/
├── Dockerfile              # Docker镜像定义
├── DEPLOYMENT.md           # 完整部署文档
├── README.md               # 本文件
├── quick_verify.sh         # 快速验证脚本
│
├── tools/                  # ReDoS检测工具（6个）
│   ├── regexploit/        # Python库，静态分析
│   ├── regexstatic/       # Java工具，静态分析
│   ├── rescue/            # Rust工具，混合分析
│   ├── rengar/            # Java工具，符号执行
│   ├── redoshunter/       # GraalVM native image
│   └── regulator/         # V8模糊测试
│
└── engines/                # 正则引擎（19个）
    ├── python/            # Python re模块
    ├── c/                 # PCRE2库
    ├── nodejs21/          # Node.js V8引擎
    ├── java11/            # Java Pattern
    ├── rust/              # Rust regex crate
    ├── re2/               # Google RE2（线性时间保证）
    └── ...                # 其他13个引擎
```

### 优势对比

**原项目问题**：
- Docker构建时编译所有组件，需要130GB内存（regulator的V8引擎编译）
- 构建时间超过2小时
- 网络不稳定导致构建失败

**重构方案优势**：
- ✅ 所有工具和引擎在宿主机预编译
- ✅ Docker镜像只复制预编译的二进制文件
- ✅ 构建时间缩短至5-10分钟
- ✅ 内存需求降至8GB以下
- ✅ Docker镜像大小：2.5GB

### 故障排除

常见问题请参考 [DEPLOYMENT.md的故障排除部分](DEPLOYMENT.md#故障排除)。

快速问题检查：

```bash
# 1. 运行快速验证脚本
bash quick_verify.sh

# 2. 检查Docker镜像
docker images | grep redos-test

# 3. 测试容器启动
docker run --rm redos-test echo "OK"

# 4. 查看工具列表
docker run --rm redos-test ls -l /app/tools/

# 5. 查看引擎列表
docker run --rm redos-test ls -l /app/engines/
```

### 贡献

如果遇到问题或有改进建议，欢迎提交Issue或Pull Request。

### 许可证

本项目基于原ReDoS测试环境重构，遵循各工具和引擎的原始许可证。

---

<a name="english"></a>
## English Documentation

### Project Overview

This is a **refactored ReDoS (Regular Expression Denial of Service) testing environment** designed to detect ReDoS vulnerabilities in regular expressions.

### Quick Start

```bash
# 1. Build Docker image (5-10 minutes)
docker build --rm -t redos-test .

# 2. Run quick verification
bash quick_verify.sh

# 3. Test a single regex
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json

# 4. View results
cat /tmp/test.json
```

### Key Features

- **6 ReDoS Detection Tools**: rescue, regexstatic, regexploit, rengar, redoshunter, regulator
- **19 Regex Engines**: Python, C (PCRE2), C++, Java 8/11, Node.js 14/21, C#, Perl, PHP, Ruby, Rust, Go, RE2, Hyperscan, etc.
- **Containerized Deployment**: All components pre-compiled for fast deployment
- **Resource Optimized**: 90% faster build time, 95% less memory required

### Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (system requirements, detailed steps, troubleshooting)
- **[CLAUDE.md](CLAUDE.md)** - Developer guide
- **quick_verify.sh** - Quick verification script

### System Requirements

- **OS**: Ubuntu 20.04/22.04 (recommended) or other Linux distributions
- **Docker**: 20.10 or higher
- **Hardware**: 4-core CPU, 8GB RAM, 20GB disk space (minimum)

### Tool Comparison

| Tool | Type | Speed | Accuracy | Use Case |
|------|------|-------|----------|----------|
| regexploit | Static analysis | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Quick screening |
| regexstatic | Static analysis | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Accurate detection |
| rescue | Hybrid analysis | ⭐⭐⭐ | ⭐⭐⭐⭐ | Balance performance & accuracy |
| rengar | Symbolic execution | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High accuracy requirements |
| redoshunter | Dynamic testing | ⭐⭐⭐ | ⭐⭐⭐⭐ | Resource-constrained environments |
| regulator | Fuzzing | ⭐⭐ | ⭐⭐⭐⭐⭐ | Comprehensive deep analysis |

### Usage Examples

#### Detect a Single Regex

```bash
# Prepare regex (base64 encoded)
REGEX="(a+)+"
REGEX_B64=$(echo -n "$REGEX" | base64)

# Use regexploit to detect (fastest)
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py $REGEX_B64 /tmp/result.json

# View results
cat /tmp/result.json
```

#### Verify Attack String

```bash
# Create test text
echo "aaaaaaaaaaaaaaaaaaaaaaaaaab" > /tmp/input.txt

# Test with Python engine
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/python/bin/benchmark $REGEX_B64 /tmp/input.txt 0
```

### Project Structure

```
ReDoSExpUniversalEnvironment/
├── Dockerfile              # Docker image definition
├── DEPLOYMENT.md           # Complete deployment documentation
├── README.md               # This file
├── quick_verify.sh         # Quick verification script
│
├── tools/                  # ReDoS detection tools (6 tools)
│   ├── regexploit/        # Python library, static analysis
│   ├── regexstatic/       # Java tool, static analysis
│   ├── rescue/            # Rust tool, hybrid analysis
│   ├── rengar/            # Java tool, symbolic execution
│   ├── redoshunter/       # GraalVM native image
│   └── regulator/         # V8 fuzzing
│
└── engines/                # Regex engines (19 engines)
    ├── python/            # Python re module
    ├── c/                 # PCRE2 library
    ├── nodejs21/          # Node.js V8 engine
    ├── java11/            # Java Pattern
    ├── rust/              # Rust regex crate
    ├── re2/               # Google RE2 (linear time guarantee)
    └── ...                # Other 13 engines
```

### Advantages

**Original Project Issues**:
- Compiles all components during Docker build, requiring 130GB memory (V8 engine compilation for regulator)
- Build time exceeds 2 hours
- Network instability causes build failures

**Refactored Solution Benefits**:
- ✅ All tools and engines pre-compiled on host
- ✅ Docker image only copies pre-compiled binaries
- ✅ Build time reduced to 5-10 minutes
- ✅ Memory requirement reduced to under 8GB
- ✅ Docker image size: 2.5GB

### Troubleshooting

For common issues, please refer to [DEPLOYMENT.md Troubleshooting section](DEPLOYMENT.md#故障排除).

Quick checks:

```bash
# 1. Run quick verification script
bash quick_verify.sh

# 2. Check Docker image
docker images | grep redos-test

# 3. Test container startup
docker run --rm redos-test echo "OK"

# 4. List tools
docker run --rm redos-test ls -l /app/tools/

# 5. List engines
docker run --rm redos-test ls -l /app/engines/
```

### Contributing

Issues and pull requests are welcome for bug reports and improvements.

### License

This project is refactored from the original ReDoS testing environment and follows the original licenses of each tool and engine.
