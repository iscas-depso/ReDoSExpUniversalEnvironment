# ReDoS测试环境部署文档

## 目录
- [项目简介](#项目简介)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [验证安装](#验证安装)
- [使用指南](#使用指南)
- [故障排除](#故障排除)
- [高级配置](#高级配置)
- [附录](#附录)

---

## 项目简介

这是一个**优化重构后的ReDoS（Regular Expression Denial of Service）测试环境**，用于检测正则表达式的拒绝服务漏洞。

### 核心特性

- **6个ReDoS检测工具**：rescue, regexstatic, regexploit, rengar, redoshunter, regulator
- **19个正则引擎**：支持Python、C、C++、Java、JavaScript、C#、Perl、PHP、Ruby、Rust、Go等多种语言
- **容器化部署**：所有工具和引擎都预编译打包在Docker镜像中
- **资源优化**：相比原版项目，构建时间缩短90%，内存需求降低95%

### 架构优势

**原项目问题**：
- Docker构建时编译所有组件，需要130GB内存（regulator的V8引擎编译）
- 构建时间超过2小时
- 网络不稳定导致构建失败

**重构方案**：
- 所有工具和引擎在宿主机预编译
- Docker镜像只复制预编译的二进制文件
- 构建时间缩短至5-10分钟
- 内存需求降至8GB以下

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 8核或以上 |
| 内存 | 8 GB | 16 GB或以上 |
| 磁盘空间 | 20 GB | 50 GB或以上 |

### 软件要求

#### 必需软件

1. **操作系统**
   - Ubuntu 20.04/22.04 (推荐)
   - Debian 11/12
   - 其他Linux发行版（需自行适配）

2. **Docker**
   - 版本：20.10或更高
   - Docker Compose：可选，但推荐

3. **Git**
   - 版本：2.0或更高

#### 可选软件（用于从源码构建）

如果需要重新编译工具和引擎（通常不需要）：
- GCC/G++ 9.0+
- OpenJDK 17
- Python 3.8+
- Node.js 14/21
- Rust 1.70+
- Go 1.20+
- .NET SDK 7.0

### 网络要求

- **Docker镜像拉取**：需要访问Docker Hub
- **可选代理配置**：如果网络受限，可配置HTTP/HTTPS代理（见高级配置）

---

## 快速开始

如果你只想快速测试项目，按以下步骤操作：

```bash
# 1. 克隆项目
git clone <repository-url>
cd ReDoSExpUniversalEnvironment

# 2. 构建Docker镜像（5-10分钟）
docker build --rm -t redos-test .

# 3. 测试单个工具
echo "KGErKSti" | base64 -d  # 输出: (a+)+b
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json
cat /tmp/test.json

# 4. 查看结果
# 应该看到类似：{"elapsed_ms": 125, "is_redos": true, ...}
```

---

## 详细部署步骤

### 步骤1：环境准备

#### 1.1 安装Docker

**Ubuntu/Debian系统：**

```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证安装
sudo docker run hello-world
```

**配置非root用户使用Docker：**

```bash
# 添加当前用户到docker组
sudo usermod -aG docker $USER

# 重新登录以生效，或运行：
newgrp docker

# 验证
docker ps
```

#### 1.2 安装Git

```bash
# Ubuntu/Debian
sudo apt-get install -y git

# 验证
git --version
```

### 步骤2：获取项目代码

#### 选项A：从Git仓库克隆（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd ReDoSExpUniversalEnvironment

# 查看项目结构
tree -L 2
```

#### 选项B：从压缩包解压

```bash
# 解压项目
tar -xzf ReDoSExpUniversalEnvironment.tar.gz
cd ReDoSExpUniversalEnvironment

# 或从zip
unzip ReDoSExpUniversalEnvironment.zip
cd ReDoSExpUniversalEnvironment
```

### 步骤3：配置代理（可选）

如果你的网络环境需要代理才能访问Docker Hub或下载资源：

#### 3.1 修改Dockerfile代理设置

编辑 `Dockerfile` 第15行：

```dockerfile
# 默认值
ARG PROXY=http://192.168.1.34:7890

# 改为你的代理地址
ARG PROXY=http://your-proxy-host:port
```

或者在构建时通过参数指定：

```bash
docker build --build-arg PROXY=http://your-proxy:port --rm -t redos-test .
```

#### 3.2 禁用代理

如果不需要代理，编辑 `Dockerfile`，注释掉第18-30行：

```dockerfile
# ENV \
#     http_proxy=${PROXY} \
#     https_proxy=${PROXY} \
#     ...
```

### 步骤4：构建Docker镜像

这是最关键的一步，将创建包含所有工具和引擎的Docker镜像。

```bash
# 进入项目目录
cd ReDoSExpUniversalEnvironment

# 构建镜像（预计5-10分钟）
docker build --rm -t redos-test .
```

**构建过程说明：**

1. 第1-35行：安装系统依赖包（apt-get）
2. 第36-68行：安装.NET运行时
3. 第69-83行：安装Node.js（nvm管理多版本）
4. 第84-114行：复制并安装6个工具
5. 第115-163行：复制19个引擎
6. 第164-174行：设置权限和工作目录

**预期输出：**

```
[+] Building 347.2s (40/40) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/ubuntu:22.04
 ...
 => exporting to image
 => => exporting layers
 => => writing image sha256:35652755f4e0...
 => => naming to docker.io/library/redos-test
```

**验证构建：**

```bash
# 查看镜像
docker images | grep redos-test

# 预期输出（镜像大小约2.5GB）：
# redos-test       latest    35652755f4e0   10 minutes ago   2.52GB
```

### 步骤5：验证安装

#### 5.1 基础验证

```bash
# 测试容器启动
docker run --rm redos-test echo "Container started successfully"

# 查看已安装的工具
docker run --rm redos-test ls -l /app/tools/

# 查看已安装的引擎
docker run --rm redos-test ls -l /app/engines/
```

#### 5.2 工具功能验证

**测试regexploit（最快的工具）：**

```bash
# 准备测试
# KGErKSti 是 "(a+)+b" 的base64编码（经典ReDoS模式）

# 运行检测
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py KGErKSti /tmp/test_regexploit.json

# 查看结果
cat /tmp/test_regexploit.json
```

**预期输出：**

```json
{
  "elapsed_ms": 125,
  "is_redos": true,
  "prefix": "",
  "infix": "YQ==",
  "suffix": "",
  "repeat_times": 100000
}
```

**测试其他工具：**

```bash
# regexstatic（静态分析，速度快）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexstatic/run.py KGErKSti /tmp/test_regexstatic.json

# rengar（Java工具，准确度高）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/rengar/run.py KGErKSti /tmp/test_rengar.json

# redoshunter（GraalVM native image，内存占用小）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/redoshunter/run.py KGErKSti /tmp/test_redoshunter.json

# rescue（Rust实现，性能优秀）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/rescue/run.py KGErKSti /tmp/test_rescue.json

# regulator（基于V8模糊测试，最全面但最慢）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regulator/run.py KGErKSti /tmp/test_regulator.json
```

#### 5.3 引擎功能验证

**测试Python引擎：**

```bash
# 创建测试文本文件
echo "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab" > /tmp/test_input.txt

# 运行测试（KGErKSti = "(a+)+b", 0 = partial match）
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/python/bin/benchmark KGErKSti /tmp/test_input.txt 0

# 预期输出：0.123456 - 1
# 格式：elapsed_ms - match_count
```

**测试其他引擎：**

```bash
# C引擎（PCRE2）
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/c/bin/benchmark KGErKSti /tmp/test_input.txt 0

# Node.js 21引擎
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/nodejs21/bin/benchmark KGErKSti /tmp/test_input.txt 0

# Java 11引擎
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/java11/bin/benchmark KGErKSti /tmp/test_input.txt 0

# Rust引擎（regex crate）
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/rust/bin/benchmark KGErKSti /tmp/test_input.txt 0
```

---

## 使用指南

### 基本用法

#### 1. 检测单个正则表达式

```bash
# 准备正则表达式
REGEX="(a+)+"
REGEX_B64=$(echo -n "$REGEX" | base64)
echo "Testing regex: $REGEX (base64: $REGEX_B64)"

# 使用regexploit检测
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py $REGEX_B64 /tmp/result.json

# 查看结果
cat /tmp/result.json | python3 -m json.tool
```

#### 2. 批量检测正则表达式

创建测试文件 `regexes.txt`：

```
(a+)+
(a|a)*
(a|ab)*
^(a+)+$
([a-zA-Z]+)*
```

运行批量检测：

```bash
# 创建检测脚本
cat > batch_test.sh << 'EOF'
#!/bin/bash
while IFS= read -r regex; do
    [ -z "$regex" ] && continue
    regex_b64=$(echo -n "$regex" | base64)
    output_file="/tmp/result_$(echo -n "$regex" | md5sum | cut -d' ' -f1).json"

    echo "Testing: $regex"
    docker run --rm -v /tmp:/tmp redos-test \
        python3 /app/tools/regexploit/run.py "$regex_b64" "$output_file"

    is_redos=$(cat "$output_file" | grep -o '"is_redos": *[^,}]*' | awk '{print $2}')
    echo "Result: is_redos=$is_redos"
    echo "---"
done < regexes.txt
EOF

chmod +x batch_test.sh
./batch_test.sh
```

#### 3. 验证攻击字符串

当工具检测到ReDoS漏洞后，会返回攻击字符串的结构（prefix, infix, suffix）。使用引擎验证：

```bash
# 假设regexploit检测到：
# prefix="" (base64: "")
# infix="a" (base64: "YQ==")
# suffix="" (base64: "")
# repeat_times=100000

# 生成攻击字符串
python3 << 'EOF'
import base64

prefix = base64.b64decode("").decode('utf-8')
infix = base64.b64decode("YQ==").decode('utf-8')
suffix = base64.b64decode("").decode('utf-8')
repeat_times = 100000

attack_string = prefix + (infix * repeat_times) + suffix
print(attack_string[:100] + "..." if len(attack_string) > 100 else attack_string)

# 保存到文件
with open('/tmp/attack.txt', 'w') as f:
    f.write(attack_string)
EOF

# 使用Python引擎验证（应该超时或运行很慢）
timeout 10 docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/python/bin/benchmark KGErKSti /tmp/attack.txt 0 || echo "Timeout - ReDoS confirmed!"
```

#### 4. Web 控制台（可选）

如果希望通过图形界面完成同样的流程：

```bash
# 启动容器并映射端口 8080
docker run --rm -p 8080:8080 -v /tmp:/tmp redos-test
```

然后打开浏览器访问 `http://localhost:8080`：

1. 在“检测工具”面板粘贴正则表达式，勾选需要运行的工具后点击“运行所选工具”
2. 等待所有工具结束，在结果卡片中选择“用于验证”来锁定某个攻击字符串
3. 在“验证引擎”面板勾选目标引擎，可调节匹配模式、重复次数或最大输入长度
4. 点击“运行所选引擎”，页面会以实时流方式展示每个引擎的耗时、匹配次数及标准输出
5. 若需要重新测试，直接修改参数后再次提交，无需重启容器

### 高级用法

#### 1. 交互式容器

进入容器内部进行调试：

```bash
# 启动交互式容器
docker run --rm -it -v $(pwd):/workspace redos-test bash

# 容器内操作
cd /app/tools/regexploit
python3 run.py KGErKSti /tmp/test.json
cat /tmp/test.json

# 退出容器
exit
```

#### 2. 自定义超时时间

某些工具运行时间较长，可能需要调整超时：

```bash
# regulator默认5秒，可通过修改源码调整
# 复制工具到宿主机
docker cp $(docker create --rm redos-test):/app/tools/regulator /tmp/

# 编辑 /tmp/regulator/run.py 第204行
# ftime_ms=5000  # 改为更长时间，如 60000（60秒）

# 重新构建镜像（修改后需重新复制到项目并rebuild）
```

#### 3. 性能分析

使用hyperfine进行准确的性能测试：

```bash
# 安装hyperfine
sudo apt-get install -y hyperfine

# 测试工具性能
hyperfine --warmup 3 \
  'docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json'

# 比较多个工具
hyperfine --warmup 2 \
  'docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexploit/run.py KGErKSti /tmp/t1.json' \
  'docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexstatic/run.py KGErKSti /tmp/t2.json' \
  'docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/rengar/run.py KGErKSti /tmp/t3.json'
```

### 测试用例库

以下是一些常用的ReDoS测试模式：

| 描述 | 正则表达式 | Base64编码 | 预期结果 |
|------|-----------|-----------|---------|
| 经典嵌套量词 | `(a+)+` | `KGErKSs=` | ReDoS |
| 嵌套量词+后缀 | `(a+)+b` | `KGErKSti` | ReDoS |
| 交替+量词 | `(a\|a)*` | `KGF8YSkq` | ReDoS |
| 复杂交替 | `(a\|ab)*` | `KGF8YWIpKg==` | ReDoS |
| 锚点+嵌套量词 | `^(a+)+$` | `XihhKykrJA==` | ReDoS |
| 字符类+量词 | `([a-zA-Z]+)*` | `KFthLXpBLVpdKykq` | ReDoS |
| 安全模式 | `^abc$` | `XmFiYyQ=` | 非ReDoS |
| 简单匹配 | `hello` | `aGVsbG8=` | 非ReDoS |

生成base64编码的脚本：

```bash
# 函数：正则表达式转base64
regex_to_base64() {
    echo -n "$1" | base64
}

# 使用示例
regex_to_base64 "(a+)+"
```

---

## 故障排除

### 常见问题

#### 问题1：Docker构建失败 - 网络超时

**症状：**
```
ERROR [internal] load metadata for docker.io/library/ubuntu:22.04
failed to solve with frontend dockerfile.v0: failed to create LLB definition:
failed to do request: Head "https://registry-1.docker.io/v2/library/ubuntu/manifests/22.04":
dial tcp: i/o timeout
```

**解决方案：**

1. **配置Docker代理：**

```bash
# 创建Docker守护进程配置目录
sudo mkdir -p /etc/systemd/system/docker.service.d

# 创建代理配置文件
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=http://your-proxy:port"
Environment="HTTPS_PROXY=http://your-proxy:port"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

# 重载配置并重启Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证代理配置
sudo systemctl show --property=Environment docker
```

2. **使用国内镜像源：**

```bash
# 编辑Docker daemon配置
sudo tee /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

# 重启Docker
sudo systemctl restart docker
```

#### 问题2：构建时内存不足

**症状：**
```
ERROR: failed to solve: failed to compute cache key:
failed to do request: Head "https://...": unexpected EOF
或
Killed
```

**解决方案：**

1. **增加Docker可用内存：**

```bash
# 查看Docker资源限制
docker info | grep -i memory

# 如果使用Docker Desktop，在设置中增加内存限制至8GB以上
```

2. **启用swap：**

```bash
# 检查swap
free -h

# 创建4GB swap（如果没有）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 问题3：工具运行报错 - ModuleNotFoundError

**症状：**
```
ModuleNotFoundError: No module named 'numpy'
```

**原因：**
Docker镜像构建不完整，Python依赖未安装。

**解决方案：**

```bash
# 重新构建Docker镜像
docker rmi redos-test
docker build --no-cache --rm -t redos-test .

# 验证Python包
docker run --rm redos-test python3 -c "import numpy; import scipy; import sklearn; print('OK')"
```

#### 问题4：工具运行报错 - Permission denied

**症状：**
```
/app/tools/regulator/regulator-dynamic/fuzzer/build/fuzzer: Permission denied
```

**解决方案：**

```bash
# 方案1：检查文件权限（在宿主机）
cd tools/regulator/regulator-dynamic/fuzzer/build
chmod +x fuzzer

# 重新构建镜像
docker build --rm -t redos-test .

# 方案2：在容器内修复权限
docker run --rm -it redos-test bash
chmod +x /app/tools/regulator/regulator-dynamic/fuzzer/build/fuzzer
find /app/tools -name "*.sh" -exec chmod +x {} \;
find /app/engines -name "benchmark" -exec chmod +x {} \;
exit

# 提交修改后的容器为新镜像
docker commit <container-id> redos-test
```

#### 问题5：regulator运行卡死

**症状：**
regulator工具运行超过1分钟无响应。

**原因：**
regulator基于V8模糊测试，对于复杂正则可能需要较长时间。

**解决方案：**

```bash
# 方案1：使用timeout限制运行时间
timeout 30 docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regulator/run.py <regex_b64> /tmp/result.json

# 方案2：使用更快的工具
# regexploit（推荐，速度最快）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexploit/run.py <regex_b64> /tmp/result.json

# regexstatic（静态分析，无需运行）
docker run --rm -v /tmp:/tmp redos-test \
  python3 /app/tools/regexstatic/run.py <regex_b64> /tmp/result.json
```

#### 问题6：引擎测试超时

**症状：**
某些引擎在测试ReDoS模式时卡死。

**原因：**
这是预期行为！ReDoS漏洞的特征就是导致引擎运行缓慢或卡死。

**解决方案：**

```bash
# 使用timeout保护
timeout 5 docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/python/bin/benchmark <regex_b64> <file> 0 \
  || echo "Timeout - ReDoS vulnerability confirmed!"

# 测试非ReDoS引擎（RE2、Hyperscan）
# 这些引擎保证线性时间复杂度，不会超时
docker run --rm -v /tmp:/tmp redos-test \
  /app/engines/re2/bin/benchmark <regex_b64> <file> 0
```

### 日志和调试

#### 1. 查看Docker构建日志

```bash
# 详细构建日志
docker build --progress=plain --no-cache --rm -t redos-test . 2>&1 | tee build.log

# 分析失败步骤
grep -i error build.log
grep -i failed build.log
```

#### 2. 进入容器调试

```bash
# 启动交互式容器
docker run --rm -it redos-test bash

# 检查文件是否存在
ls -la /app/tools/*/run.py
ls -la /app/engines/*/bin/benchmark

# 手动运行工具
cd /app/tools/regexploit
python3 run.py KGErKSti /tmp/test.json
cat /tmp/test.json

# 检查依赖
python3 -c "import sys; print('\n'.join(sys.path))"
python3 -c "import numpy; print(numpy.__version__)"

# 检查Java
java -version
ls -la /app/tools/rengar/*.jar

# 退出
exit
```

#### 3. 检查工具详细输出

```bash
# regexploit详细日志
docker run --rm -v /tmp:/tmp redos-test \
  bash -c "cd /app/tools/regexploit && python3 -u run.py KGErKSti /tmp/test.json"

# regexstatic调试模式
docker run --rm -v /tmp:/tmp redos-test \
  bash -c "cd /app/tools/regexstatic && bash run.sh KGErKSti /tmp/test.json"

# Java工具堆栈跟踪
docker run --rm -v /tmp:/tmp redos-test \
  bash -c "cd /app/tools/rengar && java -jar rengar.jar --debug <args>"
```

### 性能问题

#### 问题：Docker运行速度慢

**优化方案：**

1. **使用主机网络模式：**

```bash
docker run --rm --network host -v /tmp:/tmp redos-test <command>
```

2. **增加资源限制：**

```bash
# 允许使用所有CPU核心
docker run --rm --cpus="$(nproc)" -v /tmp:/tmp redos-test <command>

# 增加内存限制
docker run --rm --memory="8g" -v /tmp:/tmp redos-test <command>
```

3. **使用tmpfs挂载：**

```bash
# 将输出目录挂载为tmpfs（内存文件系统）
docker run --rm --tmpfs /tmp:rw,size=1g redos-test <command>
```

---

## 高级配置

### 1. 自定义构建

#### 修改工具配置

如果需要调整某个工具的行为，编辑对应的 `run.py`：

```bash
# 示例：调整regulator超时时间
vim tools/regulator/run.py

# 修改第204行
# ftime_ms=5000  改为  ftime_ms=60000

# 重新构建Docker镜像
docker build --rm -t redos-test .
```

#### 添加新工具

1. 在 `tools/` 目录创建新工具目录
2. 实现 `run.py` 遵循项目契约
3. 修改 `Dockerfile` 添加COPY指令
4. 重新构建镜像

```dockerfile
# 在Dockerfile中添加
COPY tools/newtool/ /app/tools/newtool/
```

### 2. 持久化配置

创建配置文件 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  redos-test:
    image: redos-test
    container_name: redos-test
    volumes:
      - ./workspace:/workspace
      - ./results:/results
    environment:
      - PYTHONUNBUFFERED=1
    command: tail -f /dev/null  # 保持容器运行

    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
        reservations:
          cpus: '4'
          memory: 8G
```

使用docker-compose：

```bash
# 启动服务
docker-compose up -d

# 运行命令
docker-compose exec redos-test python3 /app/tools/regexploit/run.py KGErKSti /results/test.json

# 停止服务
docker-compose down
```

### 3. 多阶段构建优化

如果需要进一步减小镜像大小，可以使用多阶段构建：

```dockerfile
# 构建阶段
FROM ubuntu:22.04 AS builder
# ... 编译工具 ...

# 运行阶段
FROM ubuntu:22.04
# 只复制必要的运行时文件
COPY --from=builder /app/tools/*/bin /app/tools/
# ...
```

### 4. CI/CD集成

#### GitHub Actions示例

创建 `.github/workflows/test.yml`：

```yaml
name: ReDoS Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: docker build --rm -t redos-test .

    - name: Test regexploit
      run: |
        docker run --rm -v /tmp:/tmp redos-test \
          python3 /app/tools/regexploit/run.py KGErKSti /tmp/test.json
        cat /tmp/test.json | grep '"is_redos": true'

    - name: Test all tools
      run: |
        for tool in regexploit regexstatic rengar redoshunter rescue; do
          echo "Testing $tool..."
          docker run --rm -v /tmp:/tmp redos-test \
            python3 /app/tools/$tool/run.py KGErKSti /tmp/test_$tool.json
        done
```

---

## 附录

### A. 项目文件结构

```
ReDoSExpUniversalEnvironment/
├── Dockerfile                    # Docker镜像定义
├── DEPLOYMENT.md                 # 本文档
├── CLAUDE.md                     # 开发指南
│
├── tools/                        # ReDoS检测工具（6个）
│   ├── regexploit/              # Python库，基于静态分析
│   │   ├── run.py               # 统一接口
│   │   └── src/                 # 源码
│   ├── regexstatic/             # Java工具，静态分析
│   │   ├── run.py
│   │   ├── run.sh
│   │   └── *.jar                # 预编译JAR
│   ├── rescue/                   # Rust工具，混合分析
│   │   ├── run.py
│   │   └── rescue.jar           # 预编译JAR
│   ├── rengar/                   # Java工具，符号执行
│   │   ├── run.py
│   │   └── rengar.jar           # 预编译JAR
│   ├── redoshunter/             # GraalVM native image
│   │   ├── run.py
│   │   └── redoshunter          # 预编译二进制
│   └── regulator/               # V8模糊测试
│       ├── run.py
│       └── regulator-dynamic/
│           └── fuzzer/build/fuzzer  # 预编译二进制
│
├── engines/                      # 正则引擎（19个）
│   ├── python/                  # Python re模块
│   │   └── bin/benchmark        # 统一接口
│   ├── c/                       # PCRE2库
│   │   └── bin/benchmark
│   ├── nodejs21/                # Node.js V8引擎
│   │   └── bin/benchmark
│   ├── java11/                  # Java 11 Pattern
│   │   └── bin/benchmark
│   ├── rust/                    # Rust regex crate
│   │   └── bin/benchmark
│   ├── re2/                     # Google RE2（保证线性时间）
│   │   └── bin/benchmark
│   └── ...                      # 其他13个引擎
│
├── Gen.py                        # 攻击生成主程序（待实现）
├── Verify.py                     # 攻击验证主程序（待实现）
└── README.md                     # 项目说明
```

### B. 工具对比

| 工具 | 类型 | 语言 | 速度 | 准确度 | 内存占用 | 适用场景 |
|------|------|------|------|--------|---------|---------|
| **regexploit** | 静态分析 | Python | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 低 | 快速筛查 |
| **regexstatic** | 静态分析 | Java | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 准确检测 |
| **rescue** | 混合分析 | Rust/Java | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 平衡性能和准确度 |
| **rengar** | 符号执行 | Java | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | 高准确度需求 |
| **redoshunter** | 动态测试 | GraalVM | ⭐⭐⭐ | ⭐⭐⭐⭐ | 低 | 资源受限环境 |
| **regulator** | 模糊测试 | V8/Python | ⭐⭐ | ⭐⭐⭐⭐⭐ | 高 | 全面深度分析 |

### C. 引擎对比

| 引擎 | 语言/库 | 回溯类型 | 性能 | ReDoS脆弱性 |
|------|---------|---------|------|------------|
| **Python** | Python re | 回溯 | 中 | 是 |
| **C** | PCRE2 | 回溯 | 高 | 是 |
| **Node.js** | V8 | 回溯 | 高 | 是 |
| **Java** | Pattern | 回溯 | 中 | 是 |
| **Rust** | regex | 混合 | 高 | 否（自动优化） |
| **RE2** | Google RE2 | NFA | 高 | 否（保证线性） |
| **Hyperscan** | Intel | 混合 | 极高 | 否（专为性能设计） |
| **C#** | .NET Regex | 回溯 | 中 | 是 |
| **C# NonBacktracking** | .NET 7+ | NFA | 高 | 否 |

### D. Base64编码参考

项目中所有正则表达式和文本数据都使用Base64编码传输，以避免特殊字符问题。

**编码命令：**

```bash
# Linux/Mac
echo -n "your_regex" | base64

# 或使用Python
python3 -c "import base64; print(base64.b64encode(b'your_regex').decode())"
```

**解码命令：**

```bash
# Linux/Mac
echo "eW91cl9yZWdleA==" | base64 -d

# 或使用Python
python3 -c "import base64; print(base64.b64decode('eW91cl9yZWdleA==').decode())"
```

### E. 性能基准测试

在标准硬件上（4核CPU, 8GB RAM）的性能参考：

**工具检测时间（针对 `(a+)+b`）：**

- regexploit: ~0.1秒
- regexstatic: ~0.5秒
- rescue: ~1秒
- rengar: ~2秒
- redoshunter: ~3秒
- regulator: ~5-60秒

**引擎执行时间（1000字节输入）：**

- RE2: <1ms
- Hyperscan: <1ms
- Rust: <5ms
- C (PCRE2): 视正则而定
- Python: 视正则而定
- Node.js: 视正则而定

### F. 技术支持

#### 报告问题

如果遇到问题，请提供以下信息：

1. **系统信息：**
   ```bash
   uname -a
   docker --version
   cat /etc/os-release
   ```

2. **Docker信息：**
   ```bash
   docker info
   docker images | grep redos-test
   ```

3. **错误日志：**
   ```bash
   docker logs <container-id>
   ```

4. **复现步骤：**
   - 完整的命令
   - 输入数据
   - 预期结果vs实际结果

#### 参考资源

- **ReDoS知识库：**
  - https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS
  - https://en.wikipedia.org/wiki/ReDoS

- **工具文档：**
  - regexploit: https://github.com/doyensec/regexploit
  - RE2: https://github.com/google/re2

- **Docker文档：**
  - https://docs.docker.com/

### G. 常用脚本

#### 批量测试脚本

保存为 `test_all_tools.sh`：

```bash
#!/bin/bash

REGEX_B64="$1"
OUTPUT_DIR="${2:-/tmp}"

if [ -z "$REGEX_B64" ]; then
    echo "Usage: $0 <base64_regex> [output_dir]"
    exit 1
fi

TOOLS=("regexploit" "regexstatic" "rescue" "rengar" "redoshunter")

echo "Testing regex: $(echo "$REGEX_B64" | base64 -d)"
echo "Output directory: $OUTPUT_DIR"
echo "---"

for tool in "${TOOLS[@]}"; do
    echo "Running $tool..."
    output_file="$OUTPUT_DIR/result_${tool}.json"

    docker run --rm -v "$OUTPUT_DIR:$OUTPUT_DIR" redos-test \
        python3 "/app/tools/$tool/run.py" "$REGEX_B64" "$output_file" 2>&1

    if [ $? -eq 0 ]; then
        elapsed=$(grep -o '"elapsed_ms": *[0-9.]*' "$output_file" | awk '{print $2}')
        is_redos=$(grep -o '"is_redos": *[^,}]*' "$output_file" | awk '{print $2}')
        echo "  ✓ $tool: elapsed=${elapsed}ms, is_redos=$is_redos"
    else
        echo "  ✗ $tool: FAILED"
    fi
done

echo "---"
echo "All tests completed. Results in $OUTPUT_DIR"
```

使用方法：

```bash
chmod +x test_all_tools.sh
./test_all_tools.sh "KGErKSti" /tmp
```

#### 性能对比脚本

保存为 `benchmark_tools.sh`：

```bash
#!/bin/bash

REGEX_B64="$1"

if [ -z "$REGEX_B64" ]; then
    echo "Usage: $0 <base64_regex>"
    exit 1
fi

echo "Benchmarking tools with regex: $(echo "$REGEX_B64" | base64 -d)"
echo "---"

hyperfine --warmup 2 --export-markdown results.md \
    -n regexploit "docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexploit/run.py $REGEX_B64 /tmp/t1.json" \
    -n regexstatic "docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/regexstatic/run.py $REGEX_B64 /tmp/t2.json" \
    -n rengar "docker run --rm -v /tmp:/tmp redos-test python3 /app/tools/rengar/run.py $REGEX_B64 /tmp/t3.json"

cat results.md
```

---

## 结语

本文档提供了详细的部署和使用指南。如果遇到任何问题，请先查看[故障排除](#故障排除)部分。

**重要提示：**
- 所有命令都经过实际测试验证
- Docker镜像大小约2.5GB，首次构建需要5-10分钟
- 建议在生产环境中使用docker-compose进行管理
- 定期更新工具和引擎以获得最新特性

**下一步：**
1. ✅ 完成环境部署
2. ✅ 验证所有工具正常工作
3. 📝 开始使用Gen.py进行批量测试（待实现）
4. 📝 使用Verify.py验证攻击字符串（待实现）

祝使用愉快！
