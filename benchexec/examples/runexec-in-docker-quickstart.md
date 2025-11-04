# runexec 在 Docker 中的最小可用教程（cgroups v2 实测）

本文给出一份可直接照做的配置与命令，确保在 Docker 容器中成功运行 BenchExec 的 `runexec`（包含容器隔离、资源限制与绑核）。以下命令均为实际验证通过的最小配置。

## 1. 准备与构建

- 需要 Docker（已在 28.x 验证）。
- 建议在 Linux/WSL2 主机上运行。
- 示例镜像与脚本已提供：`examples/runexec-docker-minimal/`

构建镜像：

```sh
docker build -t benchexec-runexec-minimal examples/runexec-docker-minimal
```

## 2. 判定 cgroups 版本（用于理解环境，不影响本教程命令）

```sh
docker run --rm alpine sh -c '
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then echo cgroups=v2; cat /sys/fs/cgroup/cgroup.controllers; else echo cgroups=v1; fi;
mount | grep cgroup || true'
```

- 看到 `cgroup2` 或存在 `/sys/fs/cgroup/cgroup.controllers` 即为 v2（本教程实测为 v2）。

## 3. 运行 runexec 的推荐目录模式

在 Docker 容器内再建隔离容器时，常见问题来自 overlay 挂载。为避免这类限制，推荐使用：

- `--read-only-dir /`（整根只读，避免在容器内做 overlay 挂载）
- `--hidden-dir /run`、`--hidden-dir /tmp`、`--hidden-dir /home`（隔离易变/临时目录，消除 HOME 创建失败告警）
- `--full-access-dir /work`（仅对工作目录放开写权限，便于在宿主直接看到输出文件）
- `--dir /work`（工作目录）

同时，为确保必要的内核能力可用（尤其 cgroups、命名空间），在 Docker 命令上使用：

- `--privileged --cap-drop=all`
- 绑定当前目录：`-v "$PWD":/work -w /work`

> 说明：在 Docker 中使用 `--privileged` 是官方文档的简化做法。生产中更推荐使用 Podman 的 rootless 方式，但本教程以稳定通过为目标。

## 4. 极简连通性测试（容器创建 + 日志）

Linux/macOS：

```sh
docker run --rm --privileged --cap-drop=all \
  -v "$PWD":/work -w /work \
  benchexec-runexec-minimal \
  runexec \
    --read-only-dir / \
    --hidden-dir /run --hidden-dir /tmp --hidden-dir /home \
    --full-access-dir /work \
    --dir /work -- /bin/sh /work/examples/runexec-docker-minimal/hello.sh
```

完成后，宿主当前目录应出现：

- `output.log`（工具标准输出）
- `output.txt`（示例脚本产物）

返回中应包含 `returnvalue=0`。

## 5. 资源限制功能（实测）

以下命令均验证通过，关键字段见 `terminationreason=...`。

- CPU 时间限制：

```sh
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --timelimit 1s --dir /work -- python -c "while True: pass"
```

预期：`terminationreason=cputime`。

- 内存限制（注意单位必须是 `MB/GB/...`，不能写 `M`）：

```sh
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --memlimit 128MB --dir /work -- \
  python -c "x=[]; import sys; [x.append(bytearray(20000000)) for _ in range(100)]"
```

预期：`terminationreason=memory` 且 `memory=128000000B`。

- 墙钟时间限制：

```sh
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --walltimelimit 1s --dir /work -- /bin/sh -c "sleep 5"
```

预期：`terminationreason=walltime`。

## 6. 绑核（--cores）验证

读取 `/proc/self/status` 的 `Cpus_allowed_list` 字段进行确认：

```sh
# 单核 0
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --cores 0 --dir /work -- \
  python -c "import sys; print(open('/proc/self/status').read())" | tee /dev/tty | grep -E "Cpus_allowed_list|returnvalue"

# 双核 0-1
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --cores 0-1 --dir /work -- \
  python -c "import sys; print(open('/proc/self/status').read())" | tee /dev/tty | grep -E "Cpus_allowed_list|returnvalue"
```

预期：分别显示 `Cpus_allowed_list: 0` 与 `Cpus_allowed_list: 0-1`。

性能小对比（可选）：

```sh
# 2 进程 CPU 密集任务（示例脚本已提供）
docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --timelimit 60s --cores 0 --output /work/output_single.log --dir /work -- \
  python /work/examples/runexec-docker-minimal/cpu_bench.py --loops 15000000 --workers 2

docker run --rm --privileged --cap-drop=all -v "$PWD":/work -w /work \
  benchexec-runexec-minimal runexec \
  --read-only-dir / --hidden-dir /run --hidden-dir /tmp --hidden-dir /home --full-access-dir /work \
  --timelimit 60s --cores 0-1 --output /work/output_dual.log --dir /work -- \
  python /work/examples/runexec-docker-minimal/cpu_bench.py --loops 15000000 --workers 2
```

对比 `output_single.log` 与 `output_dual.log`，可见双核 walltime 明显下降。

## 7. 常见问题与可选增强

- HOME 目录警告：给 `/home` 使用 `--hidden-dir` 即可消除（如上命令所示）。
- 结果文件导出：本教程通过 `--full-access-dir /work` 直接把产物写入宿主挂载目录，最简单可靠。
- 需要 overlay 行为时：可在主机和容器里安装 `fuse-overlayfs`，并在 Docker 命令添加 `--device /dev/fuse`；随后可改用 `--overlay-dir`（详见 `doc/container.md`）。
- 网络：容器内部默认禁网；若需联网可添加 `--network-access`。
- Podman（可选）：更安全的 rootless 方式，参见 `doc/benchexec-in-container.md`；命令行参数与安全选项有差异。

## 8. 关键参考

- `doc/container.md`（容器模式、目录模式、常见问题）
- `doc/runexec.md`（runexec 基本使用）
- `doc/benchexec-in-container.md`（在容器内运行 BenchExec 的背景与 Podman 建议）

