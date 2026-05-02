#!/usr/bin/env python3

import json
import math
import os
import subprocess
from pathlib import Path
from threading import Condition, Lock


PROJECT_ROOT = Path(__file__).resolve().parent
PRINT_LOCK = Lock()


def project_root():
    return PROJECT_ROOT


def print_status(message):
    with PRINT_LOCK:
        print(message, flush=True)


def default_workers():
    cpu_count = len(detect_visible_cpu_ids())
    return max(1, math.floor(cpu_count * 0.8))


def backend_command():
    backend_bin = os.environ.get("BATCH_BACKEND_BIN", "node")
    backend_script = os.environ.get("BATCH_BACKEND_SCRIPT")
    if not backend_script:
        backend_script = str(PROJECT_ROOT / "scripts" / "batch-backend.js")
    return [backend_bin, backend_script]


def parse_cpu_set_spec(value):
    if not value:
        return []

    cpu_ids = set()
    for raw_part in str(value).strip().split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            try:
                start = int(start_text)
                end = int(end_text)
            except ValueError:
                continue
            if start > end or start < 0:
                continue
            for current in range(start, end + 1):
                cpu_ids.add(current)
            continue
        try:
            cpu_id = int(part)
        except ValueError:
            continue
        if cpu_id >= 0:
            cpu_ids.add(cpu_id)

    return sorted(cpu_ids)


def detect_visible_cpu_ids():
    override = os.environ.get("BATCH_VISIBLE_CPU_IDS") or os.environ.get("CPU_ALLOCATOR_VISIBLE_CORES")
    override_ids = parse_cpu_set_spec(override)
    if override_ids:
        return override_ids

    try:
        with open("/proc/self/status", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("Cpus_allowed_list:"):
                    cpu_ids = parse_cpu_set_spec(line.split(":", 1)[1].strip())
                    if cpu_ids:
                        return cpu_ids
                    break
    except OSError:
        pass

    try:
        with open("/sys/fs/cgroup/cpuset.cpus.effective", "r", encoding="utf-8") as handle:
            cpu_ids = parse_cpu_set_spec(handle.read().strip())
            if cpu_ids:
                return cpu_ids
    except OSError:
        pass

    cpu_count = os.cpu_count() or 1
    return list(range(cpu_count))


class CpuAllocator:
    def __init__(self, visible_cpu_ids=None):
        ids = visible_cpu_ids or detect_visible_cpu_ids()
        self.visible_cpu_ids = sorted({int(cpu_id) for cpu_id in ids if int(cpu_id) >= 0})
        self.free = set(self.visible_cpu_ids)
        self.condition = Condition()

    def _try_allocate(self, count):
        if count <= 0:
            return []
        if count > len(self.free):
            return None

        free_sorted = sorted(self.free)
        start_index = 0
        while start_index < len(free_sorted):
            start = free_sorted[start_index]
            current_length = 1
            index = start_index + 1
            while index < len(free_sorted) and free_sorted[index] == free_sorted[index - 1] + 1 and current_length < count:
                current_length += 1
                index += 1
            if current_length >= count:
                allocated = list(range(start, start + count))
                for cpu_id in allocated:
                    self.free.remove(cpu_id)
                return allocated
            start_index = index

        allocated = free_sorted[:count]
        for cpu_id in allocated:
            self.free.remove(cpu_id)
        return allocated

    def acquire(self, count):
        if count <= 0:
            return []
        if count > len(self.visible_cpu_ids):
            raise ValueError(
                f"Requested {count} CPU cores, but only {len(self.visible_cpu_ids)} are visible in this container."
            )
        with self.condition:
            while True:
                allocated = self._try_allocate(count)
                if allocated is not None and len(allocated) == count:
                    return allocated
                self.condition.wait()

    def release(self, cores):
        if not cores:
            return
        with self.condition:
            for cpu_id in cores:
                if cpu_id in self.visible_cpu_ids:
                    self.free.add(cpu_id)
            self.condition.notify_all()


def run_backend(command, payload=None):
    cmd = backend_command() + [command]
    input_text = ""
    if payload is not None:
        input_text = json.dumps(payload, ensure_ascii=False)

    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )

    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or f"backend exited with {completed.returncode}"
        raise RuntimeError(error_text)

    stdout_text = completed.stdout or ""
    if not stdout_text.strip():
        raise RuntimeError("backend returned empty output")

    try:
        return parse_backend_json_output(stdout_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"backend returned invalid JSON: {exc}") from exc


def parse_backend_json_output(stdout_text):
    text = str(stdout_text or "").strip()
    if not text:
        raise json.JSONDecodeError("Expecting value", text, 0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        candidate_starts = [idx for idx, ch in enumerate(text) if ch in "{["]
        for start in reversed(candidate_starts):
            try:
                payload, end = decoder.raw_decode(text[start:])
            except json.JSONDecodeError:
                continue
            if text[start + end:].strip():
                continue
            return payload
        raise


def parse_csv_items(value):
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def parse_assignment_value(raw_value):
    text = str(raw_value).strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def parse_tool_option_assignments(assignments):
    result = {}
    for assignment in assignments or []:
        if "=" not in assignment:
            raise ValueError(f"Invalid tool option '{assignment}'. Expected TOOL.KEY=VALUE.")
        key_path, raw_value = assignment.split("=", 1)
        if "." not in key_path:
            raise ValueError(f"Invalid tool option '{assignment}'. Expected TOOL.KEY=VALUE.")
        tool_id, option_key = key_path.split(".", 1)
        tool_id = tool_id.strip()
        option_key = option_key.strip()
        if not tool_id or not option_key:
            raise ValueError(f"Invalid tool option '{assignment}'. Expected TOOL.KEY=VALUE.")
        result.setdefault(tool_id, {})[option_key] = parse_assignment_value(raw_value)
    return result
