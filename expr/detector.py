#!/usr/bin/env python3
import subprocess
import argparse
import json
import sys
from tqdm import tqdm
import multiprocessing
import base64
import uuid
from pathlib import Path
import multiprocessing.pool
import tempfile
import os
import psutil
import time
import random
import threading

# cmd = "./target/release/ere"
# cmd = "./recheck --format json"
# cmd = f"java -jar ./ReDoSHunter-1.0.0.jar"
# Default configuration (will be overridden by argparse)
cmd = None
force_fullmatch = True
timeout_seconds = 5
use_runexec = False
CPU_COUNT = 4
memory_limit = 1024
attack_size = 100
enable_cpu_monitor = True

_json_output_lock = multiprocessing.Lock()

_cpu_manager = None
_cpu_pool = None
_cpu_lock = multiprocessing.Lock()

# Global shared resource metrics for multi-process access
_mem_usage = multiprocessing.Value("f", 0.0)
_cpu_usage = multiprocessing.Array(
    "f", os.cpu_count() or 1
)  # Supporting up to 512 cores

memory_shortage = False


def _monitor_resources():
    """Background thread to update resource usage metrics periodically."""
    # Initial call to psutil to start the interval tracking
    psutil.cpu_percent(percpu=True)
    while True:
        try:
            # Update memory usage (relatively fast)
            _mem_usage.value = psutil.virtual_memory().percent
            if not memory_shortage and _mem_usage.value >= 80:
                memory_shortage = True
                print("Memory shortage detected!")
            elif memory_shortage and _mem_usage.value < 80:
                memory_shortage = False
                print("Memory shortage cleared!")

            if enable_cpu_monitor:
                # Update CPU usage for all cores (slow because of interval)
                # This blocking call happens once for all processes to share
                usages = psutil.cpu_percent(interval=0.5, percpu=True)
                for i, usage in enumerate(usages):
                    _cpu_usage[i] = usage

        except Exception:
            # Prevent the monitor thread from dying on unexpected errors
            pass
        time.sleep(0.1)


def build_string(prefix: str, infix: str, suffix: str, encoding="utf-8") -> str:
    prefix_b = base64.b64decode(prefix.encode(encoding))
    infix_b = base64.b64decode(infix.encode(encoding))
    suffix_b = base64.b64decode(suffix.encode(encoding))

    base_len = len(prefix_b) + len(suffix_b)
    if base_len > attack_size * 1024:
        raise ValueError("prefix + suffix exceeds attack size")

    if len(infix_b) == 0:
        # infix 为空，无法重复
        return prefix_b + suffix_b

    n = (attack_size * 1024 - base_len) // len(infix_b)
    return (prefix_b + infix_b * n + suffix_b).decode(encoding)


class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonPool(multiprocessing.pool.Pool):
    def Process(self, *args, **kwds):
        proc = super(NoDaemonPool, self).Process(*args, **kwds)
        proc.__class__ = NoDaemonProcess
        return proc


def init_cpu_pool():
    """Initialize the CPU pool if it has not been initialized yet."""
    global _cpu_manager, _cpu_pool
    if _cpu_pool is None:
        with _cpu_lock:
            if _cpu_pool is None:
                _cpu_manager = multiprocessing.Manager()
                _cpu_pool = _cpu_manager.Queue()
                for i in range(CPU_COUNT):
                    _cpu_pool.put(i)

                # Start the background resource monitor
                t = threading.Thread(target=_monitor_resources, daemon=True)
                t.start()


def get_cpu():
    """Acquire a CPU index (P operation). Blocks if no CPU is available."""
    cpu_id = _cpu_pool.get()

    wait_count = 0

    while True:
        # Check overall memory usage from shared value (maintained by monitor thread)
        if _mem_usage.value >= 80:
            time.sleep(random.randint(10, 30))
            continue

        # Check specific CPU core usage from shared array (maintained by monitor thread)
        if enable_cpu_monitor and _cpu_usage[cpu_id] >= 10:
            time.sleep(0.5)
            wait_count += 1
            if wait_count >= 20:
                _cpu_pool.put(cpu_id)
                return get_cpu()
            continue
        break

    return cpu_id


def return_cpu(cpu_id):
    """Release a CPU index back to the pool (V operation)."""
    _cpu_pool.put(cpu_id)


def json_output(**kwargs):
    """Print a single JSON line to stdout with a cross-process lock."""
    with _json_output_lock:
        print(json.dumps(kwargs, ensure_ascii=True), flush=True)


def run_command(args):
    filename, raw_line, idx = args
    try:
        obj = json.loads(raw_line)
    except json.JSONDecodeError:
        json_output(
            file=filename,
            line=idx,
            input=None,
            output=None,
            stdout="",
            stderr="JSON decode failed",
            return_code=None,
            timeout=False,
        )
        return

    if "input" not in obj or "output" not in obj:
        json_output(
            file=filename,
            line=idx,
            input=None,
            output=None,
            stdout="",
            stderr="missing 'input' or 'output' field",
            return_code=None,
            timeout=False,
        )
        return
    pattern = obj["input"]
    attacks = []
    try:
        attacks = json.loads(obj["output"])
        for attack in attacks:
            attack["pattern"] = pattern
            if (
                "is_redos" not in attack
                or not attack["is_redos"]
                or "prefix" not in attack
                or "suffix" not in attack
                or "infix" not in attack
            ):
                json_output(
                    file=filename,
                    line=idx,
                    input=None,
                    output="",
                    stdout="",
                    stderr="input is not a valid attack",
                    return_code=None,
                    timeout=False,
                )
                return
    except json.JSONDecodeError as e:
        json_output(
            file=filename,
            line=idx,
            input=None,
            output="",
            stdout="",
            stderr="JSON decode failed",
            return_code=None,
            timeout=False,
        )
        return
    except Exception as e:
        json_output(
            file=filename,
            line=idx,
            input=None,
            output=None,
            stdout="",
            stderr=str(e),
            return_code=None,
            timeout=False,
        )
        return
    for attack in attacks:
        tmp_path = Path(f"/tmp/{uuid.uuid4()}.txt")  # Linux / macOS
        tmp_input_path = Path(f"/tmp/{uuid.uuid4()}.txt")  # Linux / macOS
        cpu = get_cpu()
        cmds = [
            cmd,
            base64.b64encode(pattern.encode("utf-8")).decode("utf-8"),
            str(tmp_input_path),
            str(int(force_fullmatch)),
            str(tmp_path),
        ]
        if use_runexec:
            cmds = [
                "/usr/local/bin/runexec",
                "--read-only-dir",
                "/",
                "--hidden-dir",
                "/run",
                "--full-access-dir",
                "/tmp",
                "--full-access-dir",
                "/app",
                "--cores",
                str(cpu),
                "--memlimit",
                str(memory_limit * 1024 * 1024),
                "--softtimelimit",
                str(timeout_seconds),
                "--timelimit",
                str(timeout_seconds * 2),
                "--output",
                "/dev/null",
                "--",
                *cmds,
            ]
        try:
            tmp_input_path.write_text(
                build_string(attack["prefix"], attack["infix"], attack["suffix"]),
                encoding="utf-8",
            )
            # 把cmds组合在一起
            cmds = " ".join(cmds)
            result = subprocess.run(
                cmds,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds * 10,
            )

            # 如果是最后一个attack，才输出
            if attack == attacks[-1]:
                json_output(
                    file=filename,
                    line=idx,
                    input=attack,
                    output=Path(tmp_path).read_text(),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                    timeout=False,
                )

        except subprocess.TimeoutExpired as e:
            json_output(
                file=filename,
                line=idx,
                input=attacks,
                stdout="timeout",
                stderr=str(e),
                return_code=None,
                timeout=True,
            )
            return
        except Exception as e:
            json_output(
                file=filename,
                line=idx,
                input=attacks,
                output=str(e),
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                timeout=False,
            )
            return
        finally:
            return_cpu(cpu)
            tmp_path.unlink(missing_ok=True)
            tmp_input_path.unlink(missing_ok=True)


def process_file(filename, total_parts=1, part_index=0):
    print(
        f"=== Processing file: {filename} (Part {part_index+1}/{total_parts}) ===",
        file=sys.stderr,
    )

    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {filename}: {e}", file=sys.stderr)
        return

    all_commands = []
    for line in lines:
        s = line.strip()
        if s:
            data = json.loads(s)
            all_commands.append((data["file"], s, data["line"]))

    # Slice the commands according to total_parts and part_index
    total_count = len(all_commands)
    if total_parts > 1:
        chunk_size = (total_count + total_parts - 1) // total_parts
        start_idx = part_index * chunk_size
        end_idx = min(start_idx + chunk_size, total_count)
        all_commands = all_commands[start_idx:end_idx]
        print(
            f"Slicing: processing index {start_idx} to {end_idx} (Total in this part: {len(all_commands)})",
            file=sys.stderr,
        )

    if not all_commands:
        print(f"No commands to process for part {part_index}", file=sys.stderr)
        return

    # print(all_commands)
    with NoDaemonPool(processes=CPU_COUNT) as pool:
        for _ in tqdm(
            pool.imap_unordered(run_command, all_commands),
            total=len(all_commands),
            desc=f"Processing {filename} (Part {part_index+1}/{total_parts})",
        ):
            pass


def main():
    global cmd, force_fullmatch, timeout_seconds, use_runexec, memory_limit, attack_size, CPU_COUNT, enable_cpu_monitor

    parser = argparse.ArgumentParser(description="Process ReDoS experiment files.")
    parser.add_argument("files", nargs="+", help="Input files to process")
    parser.add_argument(
        "--cmd", required=True, help="Command to run (e.g., './target/release/ere')"
    )
    parser.add_argument(
        "--timeout", type=int, default=1, help="Timeout in seconds (default: 1)"
    )
    parser.add_argument(
        "--cpus", type=int, default=4, help="Number of processes to use (default: 4)"
    )
    parser.add_argument(
        "--memlimit", type=int, default=1024, help="Memory limit in MB (default: 1024)"
    )
    parser.add_argument(
        "--attack-size", type=int, default=100, help="Attack size in KB (default: 100)"
    )
    parser.add_argument(
        "--fullmatch", action="store_true", help="Use fullmatch mode in engine"
    )
    parser.add_argument("--runexec", action="store_true", help="Run using runexec")
    parser.add_argument(
        "--enable-cpu-monitor", action="store_true", help="Enable CPU monitor"
    )
    parser.add_argument(
        "--total-parts",
        type=int,
        default=1,
        help="Total number of parts to split the input into (default: 1)",
    )
    parser.add_argument(
        "--part-index",
        type=int,
        default=0,
        help="The current part index to process (0-based, default: 0)",
    )

    args = parser.parse_args()

    # Update global variables
    cmd = args.cmd
    timeout_seconds = args.timeout
    CPU_COUNT = min(args.cpus, os.cpu_count() or 1)
    force_fullmatch = args.fullmatch
    use_runexec = args.runexec
    memory_limit = args.memlimit
    attack_size = args.attack_size
    enable_cpu_monitor = args.enable_cpu_monitor

    init_cpu_pool()

    for filename in args.files:
        process_file(filename, total_parts=args.total_parts, part_index=args.part_index)


if __name__ == "__main__":
    main()
