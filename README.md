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
docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json

# 4. 查看结果
cat /tmp/test.json
```

#### Web控制台启动

```bash
# 启动容器并开放Web端口
docker run --rm --privileged --cgroupns=host -p 8080:8080 -v /tmp:/tmp redos-test

# 浏览器访问 http://localhost:8080 进入图形化界面
```

在网页中可以勾选需要的工具和引擎，先运行“检测工具”阶段获取攻击字符串，再选择其中一个结果进入“引擎验证”阶段。
如果你不需要 Web UI，而是要像旧版一样做批量处理，直接使用根目录下的 `Gen.py` 和 `Verify.py`。
默认完整测试入口是 `npm test`。它现在会依次运行 `test:unit`、`test:integration`、`test:grewia:real` 和 `test:e2e:docker`，其中后两步都依赖 Docker。
如只想做宿主上的 mock UI 快速自检，可运行 `npm run test:e2e`（基于 Playwright 的模拟端到端测试，默认使用 mock 运行器，不会真正触发真实工具或引擎）。
如果宿主机缺少 Playwright 浏览器运行库，或你希望和同类受限主机保持一致，直接改用 `npm run test:e2e:docker`；它会使用官方 Playwright 容器运行浏览器测试，不依赖宿主额外安装系统包。
如果你需要容器内真正启用 BenchExec `runexec` 的 cgroups/时间内存限制，请使用 `--privileged --cgroupns=host`。普通 `docker run` 在很多环境里会把 `/sys/fs/cgroup` 以只读方式挂进容器；当前版本不会再自动回退，而是直接以明确报错退出。
如果你还希望避免与其他容器争抢 CPU，建议同时给容器设置固定 `cpuset`。当前版本的核心分配器只会在容器“可见”的 CPU 集合里分配任务，不会越界使用其他核心。

```bash
docker run --rm --privileged --cgroupns=host \
  --cpuset-cpus=0-15 \
  -p 8080:8080 \
  -v /tmp:/tmp \
  redos-test
```

#### 默认测试链路

```bash
npm test
```

该命令会执行：
- `npm run test:unit`
- `npm run test:integration`
- `npm run test:grewia:real`
- `npm run test:e2e:docker`

说明：
- `test:grewia:real` 会在 Docker 镜像内真实执行 `/app/tools/grewia/run.py`，验证 wrapper、编译后的 GREWIA 二进制以及 `toolMeta.normalizedOptions`。
- 默认先尝试官方 `ubuntu:22.04`，若拉取超时，会顺序重试若干镜像站（如 `docker.1ms.run`、`docker.m.daocloud.io` 等）。
- `test:e2e:docker` 会在官方 Playwright 容器里运行前端端到端测试。
- 如果本机没有可用的 Docker daemon，`npm test` 会直接失败；这是有意为之，因为默认链路要求真实 GREWIA 和容器化浏览器覆盖。
- 如果只想跳过 Docker 相关测试，可使用 `npm run test:quick`。

#### Playwright 浏览器测试（适合同类受限主机）

如果宿主机满足以下任一条件，推荐直接使用容器化 Playwright 测试：
- 当前账号没有 `sudo`，无法安装浏览器依赖
- 宿主机缺少 Playwright 所需系统库，原生 `npm run test:e2e` 报 `Host system is missing dependencies to run browsers`
- 仓库工作区里曾被 root 账号运行过 Playwright，导致 `test-results/` 出现权限问题

直接执行：

```bash
npm run test:e2e:docker
```

这个命令会：
- 使用官方 Playwright 镜像运行测试
- 将浏览器测试输出写到宿主 `/tmp/redos-playwright-results`
- 使用当前用户 UID/GID 运行容器，避免再次把仓库目录写成 root

可选环境变量：

```bash
PLAYWRIGHT_DOCKER_IMAGE=mcr.microsoft.com/playwright:v1.56.0-jammy \
PLAYWRIGHT_OUTPUT_DIR=/tmp/redos-playwright-results \
PLAYWRIGHT_PORT=3100 \
npm run test:e2e:docker
```

如果网络受限导致官方镜像拉取慢，可以先手工拉取镜像，或为 `PLAYWRIGHT_DOCKER_IMAGE` 指定你所在环境可访问的等价镜像地址。

### 核心特性

- **7个ReDoS检测工具**：rescue, regexstatic, regexploit, rengar, redoshunter, regulator, GREWIA
- **19个正则引擎**：Python, C (PCRE2), C++, Java 8/11, Node.js 14/21, C#, Perl, PHP, Ruby, Rust, Go, RE2, Hyperscan等
- **容器化部署**：所有组件预编译，快速部署
- **资源优化**：构建时间缩短90%，内存需求降低95%
- **候选攻击串工作流**：工具结果既兼容 `prefix/infix/suffix/repeat_times`，也支持 `fullText` 候选列表

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

#### Web Console Workflow

```bash
# Launch the container with the dashboard
docker run --rm --privileged --cgroupns=host -p 8080:8080 -v /tmp:/tmp redos-test

# Open http://localhost:8080 in your browser
```

The dashboard lets you run detection tools in parallel, pick a generated payload, and then benchmark it against the selected engines with live progress updates.
The default full test entry point is `npm test`. It now runs `test:unit`, `test:integration`, `test:grewia:real`, and `test:e2e:docker`, so Docker is a hard requirement for the full suite.
To sanity-check the UI workflow without hitting real binaries, run `npm run test:e2e`; this launches a Playwright test suite backed by mocked tool/engine runners.
If the host is missing Playwright browser libraries or has permission issues under `test-results/`, use `npm run test:e2e:docker` to run the same suite inside the official Playwright container.
If you need BenchExec `runexec` with real cgroup-based resource limits inside Docker, start the container with `--privileged --cgroupns=host`. On many hosts, a plain `docker run` mounts `/sys/fs/cgroup` read-only; this version no longer falls back automatically and will fail fast with an explicit error instead.

#### Default Test Pipeline

```bash
npm test
```

This command runs:
- `npm run test:unit`
- `npm run test:integration`
- `npm run test:grewia:real`
- `npm run test:e2e:docker`

Notes:
- `test:grewia:real` runs the real `/app/tools/grewia/run.py` inside the project Docker image and validates the normalized GREWIA result shape.
- It tries the official `ubuntu:22.04` base image first, then retries several mirror registries automatically if the official source times out.
- `test:e2e:docker` runs Playwright inside the official browser container, so the host does not need native browser libraries.
- If Docker is unavailable, `npm test` fails fast by design.
- Use `npm run test:quick` when you only want the non-Docker unit/integration suite.

#### Batch CLI

`dev` 分支现在提供与旧版使用习惯一致的批处理入口：

```bash
# 第一阶段：批量生成攻击结果和候选
python3 Gen.py regexes.txt results.db

# 第二阶段：批量验证生成结果
python3 Verify.py results.db 64 0
```

说明：
- `Gen.py <input_file> <output_db>`：读取 txt 文件，每行一个 regex，输出 SQLite 数据库。
- `Verify.py <db_file> <max_size_kb> <match_mode>`：`match_mode` 中 `0=partial`，`1=full`。
- `Gen.py` 默认运行当前全部 tools；`Verify.py` 默认运行当前全部 `available=true` 的 engines。
- `Verify.py` 默认只验证 GREWIA 的推荐候选；如需展开全部候选，使用 `--candidate-policy all`。
- 结果库包含 `regexes`、`attack_result`、`attack_candidate`、`verify_result`、`batch_meta` 五张表。

常用参数：

```bash
# 只跑指定工具，并给 GREWIA 传专用参数
python3 Gen.py regexes.txt results.db \
  --tools regexploit,grewia \
  --tool-option grewia.regexEngine=Python \
  --tool-option grewia.candidateMode=multiple \
  --workers 8 \
  --timeout-seconds 300

# 只跑部分引擎，并验证全部 GREWIA 候选
python3 Verify.py results.db 128 1 \
  --engines python,nodejs21,re2 \
  --candidate-policy all \
  --workers 8 \
  --timeout-seconds 120
```

批处理脚本不要求先启动 Web 服务；它们会直接复用当前 `dev` 分支后端的 tool/engine 执行逻辑、GREWIA 候选模型和 `runexec` 资源限制。
如果传入 `--cpu-cores N`，`Gen.py` / `Verify.py` 会在同一个批处理进程内维护一套共享核心池，不同工具/引擎任务会共同从当前容器可见 CPU 集合里申请和释放核心，而不是各自独立记账。
要彻底避免和其他容器撞核，仍然应该在 `docker run` 时配合 `--cpuset-cpus=...` 做硬隔离。

#### Playwright Browser Tests On Restricted Hosts

Use the Dockerized Playwright runner when the host cannot run browsers natively, for example:
- no `sudo` access to install browser dependencies
- native `npm run test:e2e` fails with missing Playwright system libraries
- the repo contains root-owned files under `test-results/`

Run:

```bash
npm run test:e2e:docker
```

This wrapper:
- uses the official Playwright container image
- writes artifacts to `/tmp/redos-playwright-results` on the host
- runs as the current UID/GID so it does not reintroduce root-owned files into the workspace

Optional overrides:

```bash
PLAYWRIGHT_DOCKER_IMAGE=mcr.microsoft.com/playwright:v1.56.0-jammy \
PLAYWRIGHT_OUTPUT_DIR=/tmp/redos-playwright-results \
PLAYWRIGHT_PORT=3100 \
npm run test:e2e:docker
```

##### 资源限制与 API（Resource Limits & API）

- 界面可为“检测工具/引擎验证”分别设定：运行时间（秒）、核心数、内存（MB）。
- API：
  - `POST /api/jobs/tools`：接受 `regex`, `tools[]`，可选 `toolOptions`, `timeoutSeconds`, `cpuCores`, `memoryMB`
  - `POST /api/jobs/engines`：接受 `regex`, `engines[]`, `attack{prefix,infix,suffix,repeat_times}` 或 `attack{fullText}`，可选 `matchMode`, `repeatOverride`, `maxAttackLength`, 以及 `timeoutSeconds`, `cpuCores`, `memoryMB`
- 容器内通过 BenchExec `runexec` 施加限制。请确保 cgroups v2 子树 controller 已在容器中启用（详见 DEPLOYMENT.md 的“Runexec & cgroups v2（容器模式）”）。
- 若要让这些限制在 Docker 中可靠生效，建议使用 `docker run --privileged --cgroupns=host ...` 启动 Web 服务。
- 若要避免与其他容器共享同一批核心，建议额外加上 `--cpuset-cpus=...`。服务内部的 CPU 分配器只会在容器可见核心里分配，不会跨出这个范围。
- `toolOptions` 目前主要用于 GREWIA，可配置 `matchMode`, `attackStringLength`, `candidateMode`, `decremental`。`regexEngine` 仅为兼容旧参数保留，GREWIA 已不再做内部引擎验证。

### 项目结构

```
ReDoSExpUniversalEnvironment/
├── Dockerfile              # Docker镜像定义
├── DEPLOYMENT.md           # 完整部署文档
├── README.md               # 本文件
├── quick_verify.sh         # 快速验证脚本
│
├── tools/                  # ReDoS检测工具（7个）
│   ├── regexploit/        # Python库，静态分析
│   ├── regexstatic/       # Java工具，静态分析
│   ├── rescue/            # Rust工具，混合分析
│   ├── rengar/            # Java工具，符号执行
│   ├── redoshunter/       # GraalVM native image
│   ├── regulator/         # V8模糊测试
│   └── grewia/            # 多候选攻击串生成器（C++/Python wrapper）
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

- **7 ReDoS Detection Tools**: rescue, regexstatic, regexploit, rengar, redoshunter, regulator, GREWIA
- **19 Regex Engines**: Python, C (PCRE2), C++, Java 8/11, Node.js 14/21, C#, Perl, PHP, Ruby, Rust, Go, RE2, Hyperscan, etc.
- **Containerized Deployment**: All components pre-compiled for fast deployment
- **Resource Optimized**: 90% faster build time, 95% less memory required
- **Candidate-Payload Workflow**: tool outputs can use either the legacy `prefix/infix/suffix/repeat_times` contract or `fullText` candidate payloads

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

### API Notes

- `POST /api/jobs/tools` accepts `regex`, `tools[]`, and optional `toolOptions`, `timeoutSeconds`, `cpuCores`, `memoryMB`.
- `POST /api/jobs/engines` accepts `regex`, `engines[]`, and either `attack{prefix,infix,suffix,repeat_times}` or `attack{fullText}`.
- GREWIA-specific `toolOptions` currently include `matchMode`, `attackStringLength`, `candidateMode`, and `decremental`. `regexEngine` is retained only for backward compatibility because internal validation is disabled.

### Project Structure

```
ReDoSExpUniversalEnvironment/
├── Dockerfile              # Docker image definition
├── DEPLOYMENT.md           # Complete deployment documentation
├── README.md               # This file
├── quick_verify.sh         # Quick verification script
│
├── tools/                  # ReDoS detection tools (7 tools)
│   ├── regexploit/        # Python library, static analysis
│   ├── regexstatic/       # Java tool, static analysis
│   ├── rescue/            # Rust tool, hybrid analysis
│   ├── rengar/            # Java tool, symbolic execution
│   ├── redoshunter/       # GraalVM native image
│   ├── regulator/         # V8 fuzzing
│   └── grewia/            # Multi-candidate attack generator (C++/Python wrapper)
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
### Resource limits (BenchExec runexec)

- The web UI supports per-run limits for tool detection and engine verification: timeout in seconds, CPU cores, and memory in MB.
- The backend enforces these limits with BenchExec `runexec` parameters such as `--timelimit`, `--walltimelimit`, `--cores`, and `--memlimit`.
- This repository bundles BenchExec at `/app/benchexec`. To use it correctly in Docker, start the service with `--privileged --cgroupns=host`.
- This version does not fall back to non-cgroup execution. If cgroups are not available, the service fails fast with an explicit error message.
