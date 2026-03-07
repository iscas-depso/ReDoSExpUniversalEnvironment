#!/usr/bin/env python3
import argparse
import base64
import json
import multiprocessing
import multiprocessing.pool
import os
import random
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable, **kwargs):
        return iterable

try:
    import psutil
except Exception:
    psutil = None


timeout_seconds = 30
CPU_COUNT = 4
enable_cpu_monitor = True

_json_output_lock = multiprocessing.Lock()
_cpu_manager = None
_cpu_pool = None
_cpu_lock = multiprocessing.Lock()
_mem_usage = multiprocessing.Value("f", 0.0)
_cpu_usage = multiprocessing.Array("f", os.cpu_count() or 1)
memory_shortage = False


def _monitor_resources():
    """Background thread to update resource usage metrics periodically."""
    global memory_shortage
    psutil.cpu_percent(percpu=True)
    while True:
        try:
            _mem_usage.value = psutil.virtual_memory().percent
            if not memory_shortage and _mem_usage.value >= 80:
                memory_shortage = True
                print("Memory shortage detected!")
            elif memory_shortage and _mem_usage.value < 80:
                memory_shortage = False
                print("Memory shortage cleared!")

            if enable_cpu_monitor:
                usages = psutil.cpu_percent(interval=0.5, percpu=True)
                for i, usage in enumerate(usages):
                    _cpu_usage[i] = usage
        except Exception:
            pass
        time.sleep(0.1)


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
    global _cpu_manager, _cpu_pool
    if _cpu_pool is None:
        with _cpu_lock:
            if _cpu_pool is None:
                _cpu_manager = multiprocessing.Manager()
                _cpu_pool = _cpu_manager.Queue()
                for i in range(CPU_COUNT):
                    _cpu_pool.put(i)
                if psutil is not None:
                    t = threading.Thread(target=_monitor_resources, daemon=True)
                    t.start()


def get_cpu():
    if _cpu_pool is None:
        return 0

    cpu_id = _cpu_pool.get()
    wait_count = 0

    while True:
        if _mem_usage.value >= 80:
            time.sleep(random.randint(10, 30))
            continue

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
    _cpu_pool.put(cpu_id)


def json_output(**kwargs):
    with _json_output_lock:
        print(json.dumps(kwargs, ensure_ascii=True), flush=True)


def parse_input_line(filename, raw_line, idx):
    file_ref = filename
    line_ref = idx

    try:
        obj = json.loads(raw_line)
    except json.JSONDecodeError:
        return {
            "file": file_ref,
            "line": line_ref,
            "pattern": None,
            "error": "JSON decode failed",
        }

    if isinstance(obj, dict):
        if isinstance(obj.get("file"), str):
            file_ref = obj["file"]
        if isinstance(obj.get("line"), int):
            line_ref = obj["line"]
        pattern = obj.get("pattern")
        if isinstance(pattern, str):
            return {
                "file": file_ref,
                "line": line_ref,
                "pattern": pattern,
                "error": None,
            }

    return {
        "file": file_ref,
        "line": line_ref,
        "pattern": None,
        "error": "missing 'pattern' field",
    }


def build_command(pattern, cpu, runtime, output_path=None):
    pattern_b64 = base64.b64encode(pattern.encode("utf-8")).decode("utf-8")
    inner_cmd = [
        runtime["cmd"],
        "match",
        "-p",
        pattern_b64,
        "-b",
        "-m",
        runtime["mode_name"],
    ]

    if not runtime["use_runexec"]:
        return inner_cmd

    return [
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
        str(runtime["memory_limit"] * 1024 * 1024),
        "--softtimelimit",
        str(runtime["timeout_seconds"]),
        "--timelimit",
        str(runtime["timeout_seconds"] * 2),
        "--output",
        str(output_path),
        "--",
        *inner_cmd,
    ]


def parse_output(text):
    if not isinstance(text, str):
        raise ValueError("output is not text")

    payload = text.strip()
    if not payload:
        raise ValueError("output is empty")

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("output is empty")

        # BenchExec --output prefixes the log with command and separators.
        # The ere CLI prints a single-line JSON object, so parse the last
        # non-empty line as the actual tool output.
        parsed = json.loads(lines[-1])

    if not isinstance(parsed, dict):
        raise ValueError("output JSON is not an object")
    return parsed


def run_command(task):
    runtime = task["runtime"]
    cpu = get_cpu()
    tmp_output_path = Path(f"/tmp/{uuid.uuid4()}.txt")

    try:
        parsed = parse_input_line(task["filename"], task["raw_line"], task["line_no"])
        if parsed["error"] is not None:
            json_output(
                file=parsed["file"],
                line=parsed["line"],
                pattern=parsed["pattern"],
                mode=runtime["mode_name"],
                output=None,
                stdout="",
                stderr=parsed["error"],
                return_code=None,
                timeout=False,
            )
            return

        cmds = build_command(parsed["pattern"], cpu, runtime, tmp_output_path)
        result = subprocess.run(
            cmds,
            capture_output=True,
            text=True,
            timeout=runtime["timeout_seconds"] * 10,
        )

        output_obj = None
        stderr_text = result.stderr
        output_text = result.stdout

        if runtime["use_runexec"]:
            if tmp_output_path.exists():
                output_text = tmp_output_path.read_text(encoding="utf-8")
            elif result.returncode == 0:
                stderr_text = f"{stderr_text}\nmissing runexec output file: {tmp_output_path}".strip()

        if result.returncode == 0 and output_text.strip():
            try:
                output_obj = parse_output(output_text)
            except Exception as e:
                stderr_text = f"{stderr_text}\nparse output failed: {e}".strip()

        json_output(
            file=parsed["file"],
            line=parsed["line"],
            pattern=parsed["pattern"],
            mode=runtime["mode_name"],
            output=output_obj,
            stdout=result.stdout,
            stderr=stderr_text,
            return_code=result.returncode,
            timeout=False,
        )
    except subprocess.TimeoutExpired as e:
        json_output(
            file=task["file_ref"],
            line=task["line_ref"],
            pattern=task["pattern_ref"],
            mode=runtime["mode_name"],
            output=None,
            stdout="",
            stderr=str(e),
            return_code=None,
            timeout=True,
        )
    except Exception as e:
        json_output(
            file=task["file_ref"],
            line=task["line_ref"],
            pattern=task["pattern_ref"],
            mode=runtime["mode_name"],
            output=None,
            stdout="",
            stderr=str(e),
            return_code=None,
            timeout=False,
        )
    finally:
        return_cpu(cpu)
        tmp_output_path.unlink(missing_ok=True)


def process_file(filename, runtime, total_parts=1, part_index=0):
    print(
        f"=== Processing file: {filename} (Part {part_index+1}/{total_parts}) ===",
        file=sys.stderr,
    )

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {filename}: {e}", file=sys.stderr)
        return

    all_commands = []
    for idx, raw_line in enumerate(lines):
        if not raw_line.strip():
            continue
        preview = parse_input_line(filename, raw_line, idx)
        all_commands.append(
            {
                "filename": filename,
                "raw_line": raw_line.strip(),
                "line_no": idx,
                "file_ref": preview["file"],
                "line_ref": preview["line"],
                "pattern_ref": preview["pattern"],
                "runtime": runtime,
            }
        )

    all_commands.sort(key=lambda x: (str(x["file_ref"]), x["line_ref"], x["line_no"]))

    total_count = len(all_commands)
    if total_parts > 1:
        if part_index < 0 or part_index >= total_parts:
            print(
                f"Part index {part_index} out of range for total_parts={total_parts}; skip.",
                file=sys.stderr,
            )
            return
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

    with NoDaemonPool(processes=CPU_COUNT) as pool:
        for _ in tqdm(
            pool.imap_unordered(run_command, all_commands),
            total=len(all_commands),
            desc=f"Processing {filename} (Part {part_index+1}/{total_parts})",
        ):
            pass


def main():
    global timeout_seconds, CPU_COUNT, enable_cpu_monitor

    parser = argparse.ArgumentParser(
        description="Construct NFA/DFA sizes for regex datasets."
    )
    parser.add_argument("files", nargs="+", help="Input JSONL files to process")
    parser.add_argument("--cmd", required=True, help="Path to ere binary")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["nfa", "dfa"],
        help="Construction mode to execute",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--cpus", type=int, default=4, help="Number of processes to use (default: 4)"
    )
    parser.add_argument(
        "--memlimit", type=int, default=1024, help="Memory limit in MB (default: 1024)"
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

    timeout_seconds = args.timeout
    CPU_COUNT = max(1, min(args.cpus, os.cpu_count() or 1))
    enable_cpu_monitor = args.enable_cpu_monitor

    runtime = {
        "cmd": args.cmd,
        "mode_name": args.mode,
        "timeout_seconds": args.timeout,
        "use_runexec": args.runexec,
        "memory_limit": args.memlimit,
    }

    init_cpu_pool()

    for filename in args.files:
        process_file(filename, runtime, total_parts=args.total_parts, part_index=args.part_index)


if __name__ == "__main__":
    main()
