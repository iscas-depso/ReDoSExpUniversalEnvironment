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

# Default configuration (overridden by argparse)
cmd = None
force_fullmatch = True
timeout_seconds = 5
use_runexec = False
CPU_COUNT = 4
memory_limit = 1024
enable_cpu_monitor = True

# Linearity experiment configuration
ks = [50, 200, 800, 2000, 4000, 5000, 12000, 50000, 150000, 500000]
runs_per_k = 7
sample_count = 30
seed = 20260306
required_engines = ["python", "java11", "nodejs14", "ere"]
engine_name = "unknown"
manifest_path = None
write_manifest_path = None

_json_output_lock = multiprocessing.Lock()

_cpu_manager = None
_cpu_pool = None
_cpu_lock = multiprocessing.Lock()

# Shared resource metrics
_mem_usage = multiprocessing.Value("f", 0.0)
_cpu_usage = multiprocessing.Array("f", os.cpu_count() or 1)

memory_shortage = False


def _monitor_resources():
    """Background thread to update resource usage metrics periodically."""
    global memory_shortage

    if psutil is None:
        return

    psutil.cpu_percent(percpu=True)
    while True:
        try:
            _mem_usage.value = psutil.virtual_memory().percent
            if not memory_shortage and _mem_usage.value >= 80:
                memory_shortage = True
                print("Memory shortage detected!", file=sys.stderr)
            elif memory_shortage and _mem_usage.value < 80:
                memory_shortage = False
                print("Memory shortage cleared!", file=sys.stderr)

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
    """Initialize CPU token pool if it has not been initialized."""
    global _cpu_manager, _cpu_pool
    if _cpu_pool is None:
        with _cpu_lock:
            if _cpu_pool is None:
                _cpu_manager = None
                _cpu_pool = multiprocessing.Queue()
                for i in range(CPU_COUNT):
                    _cpu_pool.put(i)

                if psutil is not None:
                    t = threading.Thread(target=_monitor_resources, daemon=True)
                    t.start()


def get_cpu():
    """Acquire a CPU index (P operation). Blocks if no CPU is available."""
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
    """Release a CPU index back to the pool (V operation)."""
    if _cpu_pool is None:
        return
    _cpu_pool.put(cpu_id)


def json_output(**kwargs):
    """Print one JSON line to stdout with a cross-process lock."""
    with _json_output_lock:
        print(json.dumps(kwargs, ensure_ascii=True), flush=True)


def decode_b64_text(s: str) -> str:
    return base64.b64decode(s.encode("utf-8")).decode("utf-8")


def decode_b64_bytes(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))


def quantile_edges(values, bins=3):
    if not values:
        return [0.0] * (bins + 1)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    edges = [float(sorted_vals[0])]
    for i in range(1, bins):
        idx = int(round((n - 1) * i / bins))
        edges.append(float(sorted_vals[idx]))
    edges.append(float(sorted_vals[-1]))
    for i in range(1, len(edges)):
        if edges[i] < edges[i - 1]:
            edges[i] = edges[i - 1]
    return edges


def assign_bin(v, edges):
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i == len(edges) - 2:
            if lo <= v <= hi:
                return i
        elif lo <= v < hi:
            return i
    return len(edges) - 2


def choose_attack_from_record(record):
    """Pick one attack per record: prefer repeat_times>0, then shortest infix bytes."""
    details = record.get("engine_details", {})
    if not isinstance(details, dict):
        return None

    candidates = []
    dedup = set()
    for ed in details.values():
        if not isinstance(ed, dict):
            continue
        attacks = ed.get("successful_attacks", [])
        if not isinstance(attacks, list):
            continue
        for attack in attacks:
            if not isinstance(attack, dict):
                continue
            if attack.get("is_redos") is not True:
                continue
            prefix = attack.get("prefix")
            infix = attack.get("infix")
            suffix = attack.get("suffix")
            if not (isinstance(prefix, str) and isinstance(infix, str) and isinstance(suffix, str)):
                continue

            key = (prefix, infix, suffix)
            if key in dedup:
                continue

            try:
                infix_b = decode_b64_bytes(infix)
                _ = decode_b64_text(prefix)
                _ = decode_b64_text(infix)
                _ = decode_b64_text(suffix)
            except Exception:
                continue

            if len(infix_b) == 0:
                continue

            repeat_times = attack.get("repeat_times")
            valid_repeat = isinstance(repeat_times, int) and repeat_times > 0
            dedup.add(key)
            candidates.append(
                {
                    "prefix": prefix,
                    "infix": infix,
                    "suffix": suffix,
                    "infix_byte_len": len(infix_b),
                    "repeat_positive": valid_repeat,
                }
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            0 if x["repeat_positive"] else 1,
            x["infix_byte_len"],
        )
    )
    return candidates[0]


def select_samples(lines, filename):
    """Filter and stratified-sample records. Return commands for execution."""
    required = set(required_engines)
    candidates = []

    for idx, raw in enumerate(lines, start=1):
        s = raw.strip()
        if not s:
            continue

        try:
            rec = json.loads(s)
        except json.JSONDecodeError:
            continue

        engines = rec.get("engines", [])
        pattern = rec.get("pattern")
        src_file = rec.get("file")
        src_line = rec.get("line")

        if not isinstance(engines, list):
            continue
        if not required.issubset(set(engines)):
            continue
        if not (isinstance(pattern, str) and isinstance(src_file, str) and isinstance(src_line, int)):
            continue

        picked = choose_attack_from_record(rec)
        if picked is None:
            continue

        candidates.append(
            {
                "filename": filename,
                "gt_row": idx,
                "file": src_file,
                "line": src_line,
                "pattern": pattern,
                "engines": engines,
                "prefix": picked["prefix"],
                "infix": picked["infix"],
                "suffix": picked["suffix"],
                "infix_byte_len": picked["infix_byte_len"],
                "pattern_len": len(pattern),
                "sample_id": f"{Path(src_file).name}:{src_line}",
            }
        )

    if not candidates:
        return []

    infix_edges = quantile_edges([c["infix_byte_len"] for c in candidates], bins=3)
    pattern_edges = quantile_edges([c["pattern_len"] for c in candidates], bins=3)

    strata = {}
    for c in candidates:
        ib = assign_bin(c["infix_byte_len"], infix_edges)
        pb = assign_bin(c["pattern_len"], pattern_edges)
        strata.setdefault((ib, pb), []).append(c)

    rng = random.Random(seed)
    keys = sorted(strata.keys())
    for k in keys:
        rng.shuffle(strata[k])

    target = min(sample_count, len(candidates))
    selected = []

    while len(selected) < target:
        progressed = False
        for k in keys:
            bucket = strata[k]
            if bucket:
                selected.append(bucket.pop())
                progressed = True
                if len(selected) >= target:
                    break
        if not progressed:
            break

    selected.sort(key=lambda x: (x["file"], x["line"], x["sample_id"]))
    return selected


def select_samples_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise RuntimeError(f"Error reading file {filename}: {e}")
    return select_samples(lines, filename)


def write_manifest(path, commands):
    meta = {
        "type": "meta",
        "version": 1,
        "seed": seed,
        "samples": sample_count,
        "required_engines": required_engines,
        "ks": ks,
        "runs_per_k": runs_per_k,
        "count": len(commands),
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=True) + "\n")
        for c in commands:
            row = dict(c)
            row["type"] = "sample"
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def load_manifest(path):
    meta = None
    commands = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            if not isinstance(obj, dict):
                continue
            typ = obj.get("type")
            if typ == "meta":
                meta = obj
            elif typ == "sample":
                commands.append(obj)
    if meta is None:
        raise RuntimeError("manifest missing meta line")
    return meta, commands


def validate_manifest(meta):
    mismatches = []
    if int(meta.get("seed", -1)) != int(seed):
        mismatches.append(f"seed: manifest={meta.get('seed')} cli={seed}")
    if int(meta.get("samples", -1)) != int(sample_count):
        mismatches.append(f"samples: manifest={meta.get('samples')} cli={sample_count}")
    if list(meta.get("required_engines", [])) != list(required_engines):
        mismatches.append(
            f"required_engines: manifest={meta.get('required_engines')} cli={required_engines}"
        )
    if list(meta.get("ks", [])) != list(ks):
        mismatches.append(f"ks: manifest={meta.get('ks')} cli={ks}")
    if int(meta.get("runs_per_k", -1)) != int(runs_per_k):
        mismatches.append(
            f"runs_per_k: manifest={meta.get('runs_per_k')} cli={runs_per_k}"
        )
    if mismatches:
        raise RuntimeError("manifest config mismatch: " + "; ".join(mismatches))


def build_input_from_attack(prefix_b64, infix_b64, suffix_b64, k):
    prefix = decode_b64_text(prefix_b64)
    infix = decode_b64_text(infix_b64)
    suffix = decode_b64_text(suffix_b64)
    text = prefix + infix * k + suffix
    return text, len(text.encode("utf-8"))


def run_single_execution(pattern, input_text, cpu, runtime):
    tmp_input_path = Path(f"/tmp/{uuid.uuid4()}.txt")
    tmp_output_path = Path(f"/tmp/{uuid.uuid4()}.txt")

    pattern_to_run = pattern
    if runtime["force_fullmatch"]:
        pattern_to_run = f"^(?:{pattern})$"

    cmds = [
        runtime["cmd"],
        base64.b64encode(pattern_to_run.encode("utf-8")).decode("utf-8"),
        str(tmp_input_path),
        str(int(runtime["force_fullmatch"])),
        str(tmp_output_path),
    ]

    if runtime["use_runexec"]:
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
            str(runtime["memory_limit"] * 1024 * 1024),
            "--softtimelimit",
            str(runtime["timeout_seconds"]),
            "--timelimit",
            str(runtime["timeout_seconds"] * 2),
            "--output",
            "/dev/null",
            "--",
            *cmds,
        ]

    result = None
    try:
        tmp_input_path.write_text(input_text, encoding="utf-8")

        cmdline = " ".join(cmds)
        result = subprocess.run(
            cmdline,
            shell=True,
            capture_output=True,
            text=True,
            timeout=runtime["timeout_seconds"] * 10,
        )

        output_text = ""
        if tmp_output_path.exists():
            output_text = tmp_output_path.read_text(encoding="utf-8")

        return {
            "timeout": False,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output": output_text,
        }

    except subprocess.TimeoutExpired as e:
        return {
            "timeout": True,
            "return_code": None,
            "stdout": "",
            "stderr": str(e),
            "output": "timeout",
        }
    except Exception as e:
        return {
            "timeout": False,
            "return_code": None if result is None else result.returncode,
            "stdout": "" if result is None else result.stdout,
            "stderr": str(e) if result is None else result.stderr,
            "output": str(e),
        }
    finally:
        tmp_input_path.unlink(missing_ok=True)
        tmp_output_path.unlink(missing_ok=True)


def run_command(task):
    """Execute one sampled record over ks and runs, print JSON lines per run."""
    runtime = task["runtime"]
    timeout_nonwarmup = 0
    measured_runs = max(0, runtime["runs_per_k"] - 1)

    for k in runtime["ks"]:
        input_text, input_bytes = build_input_from_attack(
            task["prefix"], task["infix"], task["suffix"], k
        )

        timeout_nonwarmup = 0
        for run_id in range(runtime["runs_per_k"]):
            warmup = run_id == 0
            cpu = get_cpu()
            try:
                ret = run_single_execution(task["pattern"], input_text, cpu, runtime)
            finally:
                return_cpu(cpu)

            json_output(
                file=task["file"],
                line=task["line"],
                gt_file=task["filename"],
                gt_row=task["gt_row"],
                sample_id=task["sample_id"],
                engine=runtime["engine_name"],
                input={
                    "pattern": task["pattern"],
                    "prefix": task["prefix"],
                    "infix": task["infix"],
                    "suffix": task["suffix"],
                },
                k=k,
                input_bytes=input_bytes,
                run_id=run_id,
                warmup=warmup,
                output=ret["output"],
                stdout=ret["stdout"],
                stderr=ret["stderr"],
                return_code=ret["return_code"],
                timeout=ret["timeout"],
            )

            if (not warmup) and ret["timeout"]:
                timeout_nonwarmup += 1

        # Dynamic truncation for this sample on this engine
        if measured_runs > 0 and timeout_nonwarmup >= max(1, measured_runs // 2):
            break


def process_commands(all_commands, label, total_parts=1, part_index=0):
    print(
        f"=== Processing: {label} (Part {part_index + 1}/{total_parts}) ===",
        file=sys.stderr,
    )

    total_candidates = len(all_commands)

    if total_parts > 1:
        if part_index >= total_parts:
            print(
                f"Part index {part_index} out of range for total_parts={total_parts}; skip.",
                file=sys.stderr,
            )
            return
        chunk_size = (total_candidates + total_parts - 1) // total_parts
        start_idx = part_index * chunk_size
        end_idx = min(start_idx + chunk_size, total_candidates)
        all_commands = all_commands[start_idx:end_idx]
        print(
            f"Slicing: processing index {start_idx} to {end_idx} (Total in this part: {len(all_commands)})",
            file=sys.stderr,
        )

    print(
        f"Selected samples: {total_candidates}, executing in this part: {len(all_commands)}",
        file=sys.stderr,
    )

    if not all_commands:
        print(f"No commands to process for part {part_index}", file=sys.stderr)
        return

    runtime = {
        "cmd": cmd,
        "engine_name": engine_name,
        "force_fullmatch": force_fullmatch,
        "timeout_seconds": timeout_seconds,
        "use_runexec": use_runexec,
        "memory_limit": memory_limit,
        "ks": ks,
        "runs_per_k": runs_per_k,
    }
    for x in all_commands:
        x["runtime"] = runtime

    with NoDaemonPool(processes=CPU_COUNT) as pool:
        for _ in tqdm(
            pool.imap_unordered(run_command, all_commands),
            total=len(all_commands),
            desc=f"Processing {label} (Part {part_index + 1}/{total_parts})",
        ):
            pass


def process_file(filename, total_parts=1, part_index=0):
    all_commands = select_samples_from_file(filename)
    process_commands(
        all_commands,
        label=filename,
        total_parts=total_parts,
        part_index=part_index,
    )


def parse_engine_cmd(value):
    if "=" in value:
        lhs, rhs = value.split("=", 1)
        return lhs.strip(), rhs.strip()
    return None, value


def main():
    global cmd, force_fullmatch, timeout_seconds, use_runexec
    global memory_limit, CPU_COUNT, enable_cpu_monitor
    global ks, runs_per_k, sample_count, seed, required_engines, engine_name

    parser = argparse.ArgumentParser(
        description="Linearity benchmark using ground-truth attacks (detect/expr style)."
    )
    parser.add_argument("files", nargs="*", help="Ground-truth JSONL files")
    parser.add_argument("--cmd", required=True, help="Benchmark command path")
    parser.add_argument("--engine", default="unknown", help="Engine name in output")
    parser.add_argument(
        "--timeout", type=int, default=5, help="Timeout in seconds (default: 5)"
    )
    parser.add_argument(
        "--cpus", type=int, default=4, help="Number of processes (default: 4)"
    )
    parser.add_argument(
        "--memlimit", type=int, default=1024, help="Memory limit in MB (default: 1024)"
    )
    parser.add_argument("--fullmatch", action="store_true", help="Use fullmatch mode")
    parser.add_argument("--runexec", action="store_true", help="Run using runexec")
    parser.add_argument(
        "--enable-cpu-monitor", action="store_true", help="Enable CPU monitor"
    )

    parser.add_argument(
        "--samples", type=int, default=30, help="Sample count after stratified sampling"
    )
    parser.add_argument("--seed", type=int, default=20260306, help="Sampling seed")
    parser.add_argument(
        "--ks",
        type=int,
        nargs="+",
        default=[50, 200, 800, 2000, 4000, 5000, 12000, 50000, 150000, 500000],
        help="Infix repeat grid",
    )
    parser.add_argument(
        "--runs-per-k",
        type=int,
        default=7,
        help="Runs per k (run_id=0 is warmup)",
    )
    parser.add_argument(
        "--required-engines",
        nargs="+",
        default=["python", "java11", "nodejs14"],
        help="Only use records containing all required engines",
    )

    parser.add_argument(
        "--total-parts",
        type=int,
        default=1,
        help="Total number of split parts (default: 1)",
    )
    parser.add_argument(
        "--part-index",
        type=int,
        default=0,
        help="Current part index (0-based, default: 0)",
    )
    parser.add_argument(
        "--write-manifest",
        type=str,
        default=None,
        help="Write sampled commands to manifest JSONL and exit",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Read sampled commands from manifest JSONL instead of re-sampling",
    )

    args = parser.parse_args()

    cmd = args.cmd
    timeout_seconds = args.timeout
    CPU_COUNT = min(args.cpus, os.cpu_count() or 1)
    force_fullmatch = args.fullmatch
    use_runexec = args.runexec
    memory_limit = args.memlimit
    enable_cpu_monitor = args.enable_cpu_monitor

    ks = sorted(set(args.ks))
    runs_per_k = max(1, args.runs_per_k)
    sample_count = max(1, args.samples)
    seed = args.seed
    required_engines = args.required_engines
    engine_name = args.engine
    manifest_path = args.manifest
    write_manifest_path = args.write_manifest

    if manifest_path and write_manifest_path:
        raise RuntimeError("--manifest and --write-manifest cannot be used together")

    init_cpu_pool()
    total_parts = max(1, args.total_parts)
    part_index = max(0, args.part_index)

    if write_manifest_path:
        if not args.files:
            raise RuntimeError("--write-manifest requires at least one input file")
        all_commands = []
        for filename in args.files:
            all_commands.extend(select_samples_from_file(filename))
        all_commands.sort(key=lambda x: (x["file"], x["line"], x["sample_id"]))
        manifest_out = Path(write_manifest_path)
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        write_manifest(str(manifest_out), all_commands)
        print(
            f"Wrote manifest: {manifest_out} (samples={len(all_commands)})",
            file=sys.stderr,
        )
        return

    if manifest_path:
        meta, all_commands = load_manifest(manifest_path)
        validate_manifest(meta)
        process_commands(
            all_commands,
            label=f"manifest:{manifest_path}",
            total_parts=total_parts,
            part_index=part_index,
        )
        return

    if not args.files:
        raise RuntimeError("No input files provided")

    for filename in args.files:
        process_file(filename, total_parts=total_parts, part_index=part_index)


if __name__ == "__main__":
    main()
