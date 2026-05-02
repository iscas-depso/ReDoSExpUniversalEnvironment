#!/usr/bin/env python3

import argparse
import base64
import json
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

from batch_common import CpuAllocator, default_workers, detect_visible_cpu_ids, parse_csv_items, parse_tool_option_assignments, print_status, run_backend


SCHEMA_VERSION = 3
DB_LOCK = Lock()
MAX_INFRA_RETRIES = 3


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Batch ReDoS attack generation")
    parser.add_argument("input_file", help="Input txt file with one regex per line")
    parser.add_argument("output_db", help="Output sqlite database path")
    parser.add_argument("--tools", help="Comma-separated tool ids; default: all available tools")
    parser.add_argument("--workers", type=int, default=default_workers(), help="Concurrent workers")
    parser.add_argument("--timeout-seconds", type=int, help="Per-tool timeout in seconds")
    parser.add_argument("--cpu-cores", type=int, help="CPU cores passed to runexec")
    parser.add_argument("--memory-mb", type=int, help="Memory limit in MB passed to runexec")
    parser.add_argument(
        "--tool-option",
        action="append",
        default=[],
        help="Per-tool option in TOOL.KEY=VALUE form; may be repeated"
    )
    return parser


def ensure_positive(value, field_name):
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return value


def load_regexes(input_path):
    regexes = []
    with open(input_path, "r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            regex = raw_line.strip()
            if not regex:
                continue
            regexes.append({
                "id": line_no,
                "source_line": line_no,
                "regex": regex,
                "base64regex": base64.b64encode(regex.encode("utf-8")).decode("utf-8")
            })
    return regexes


def setup_database(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE regexes (
                id INTEGER PRIMARY KEY,
                regex TEXT NOT NULL,
                base64regex TEXT NOT NULL,
                source_line INTEGER NOT NULL
            );

            CREATE TABLE attack_result (
                tool TEXT NOT NULL,
                id INTEGER NOT NULL,
                status TEXT NOT NULL,
                is_redos INTEGER NOT NULL,
                prefix TEXT,
                infix TEXT,
                suffix TEXT,
                repeat_times INTEGER,
                elapsed_ms INTEGER,
                time REAL,
                time_source TEXT,
                walltime_ms REAL,
                cputime_ms REAL,
                memory_bytes INTEGER,
                full_json TEXT,
                logs_json TEXT,
                error_json TEXT,
                error_type TEXT,
                termination_reason TEXT,
                return_value INTEGER,
                raw_output TEXT,
                PRIMARY KEY (tool, id),
                FOREIGN KEY (id) REFERENCES regexes(id)
            );

            CREATE TABLE attack_candidate (
                tool TEXT NOT NULL,
                id INTEGER NOT NULL,
                candidate_id TEXT NOT NULL,
                candidate_label TEXT,
                is_recommended INTEGER NOT NULL,
                attack_type TEXT NOT NULL,
                full_text TEXT,
                prefix TEXT,
                infix TEXT,
                suffix TEXT,
                repeat_times INTEGER,
                payload_length INTEGER,
                preview TEXT,
                metadata_json TEXT,
                PRIMARY KEY (tool, id, candidate_id),
                FOREIGN KEY (id) REFERENCES regexes(id)
            );

            CREATE TABLE verify_result (
                tool TEXT NOT NULL,
                id INTEGER NOT NULL,
                engine TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                status TEXT NOT NULL,
                elapsed_ms INTEGER,
                match_count INTEGER,
                stdout TEXT,
                stderr TEXT,
                raw_output TEXT,
                logs_json TEXT,
                attack_source_json TEXT,
                PRIMARY KEY (tool, id, engine, candidate_id),
                FOREIGN KEY (id) REFERENCES regexes(id)
            );

            CREATE TABLE batch_meta (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def upsert_meta(conn, key, value):
    conn.execute(
        """
        INSERT INTO batch_meta (key, value_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
        """,
        (key, json.dumps(value, ensure_ascii=False))
    )


def insert_regexes(db_path, regexes):
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            "INSERT INTO regexes (id, regex, base64regex, source_line) VALUES (?, ?, ?, ?)",
            [(item["id"], item["regex"], item["base64regex"], item["source_line"]) for item in regexes]
        )
        conn.commit()
    finally:
        conn.close()


def normalize_selected_tools(meta, requested_tools):
    tool_map = {tool["id"]: tool for tool in meta.get("tools", [])}
    if requested_tools:
        selected = parse_csv_items(requested_tools)
    else:
        selected = list(tool_map.keys())

    if not selected:
        raise ValueError("No tools selected.")

    unsupported = [tool_id for tool_id in selected if tool_id not in tool_map]
    if unsupported:
        raise ValueError(f"Unsupported tools: {', '.join(unsupported)}")
    return selected, tool_map


def validate_tool_options(tool_options, selected_tools, tool_map):
    for tool_id in tool_options:
        if tool_id not in tool_map:
            raise ValueError(f"Unsupported tool in --tool-option: {tool_id}")
        if tool_id not in selected_tools:
            raise ValueError(f"--tool-option provided for unselected tool: {tool_id}")


def completed_with_missing_metrics(result):
    if result.get("status") != "completed":
        return False
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    return (
        output.get("walltime_ms") is None
        or output.get("cputime_ms") is None
        or output.get("memory_bytes") is None
    )


def retryable_infra_metrics_gap(result):
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    if not output:
        return False
    metrics_missing = (
        output.get("walltime_ms") is None
        or output.get("cputime_ms") is None
        or output.get("memory_bytes") is None
    )
    if not metrics_missing:
        return False
    if result.get("status") == "completed":
        return True
    error = result.get("error") if isinstance(result.get("error"), dict) else {}
    return result.get("status") == "inconclusive" and error.get("type") == "infra_error"


def mark_inconclusive_infra(result, attempts):
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    result["status"] = "inconclusive"
    existing_error = result.get("error") if isinstance(result.get("error"), dict) else {}
    result["error"] = {
        **existing_error,
        "message": "runexec did not provide complete metrics for successful tool execution after retries.",
        "type": "infra_error",
        "time": output.get("time"),
        "timeSource": output.get("time_source"),
        "walltimeMs": output.get("walltime_ms"),
        "cputimeMs": output.get("cputime_ms"),
        "memoryBytes": output.get("memory_bytes"),
        "attempts": attempts
    }
    return result


def write_attack_result(db_path, regex_record, tool_id, result):
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    error = result.get("error") if isinstance(result.get("error"), dict) else {}
    candidates = output.get("candidates") if isinstance(output.get("candidates"), list) else []
    recommended_id = output.get("recommendedCandidateId")
    if candidates and not recommended_id:
        recommended_id = candidates[0].get("id")

    is_redos = 1 if output.get("is_redos") or candidates else 0
    elapsed_ms = output.get("elapsed_ms")
    if elapsed_ms is None:
        elapsed_ms = result.get("elapsedMs")
    effective_time = output.get("time")
    if effective_time is None:
        effective_time = error.get("time")
    time_source = output.get("time_source")
    if time_source is None:
        time_source = error.get("timeSource")
    walltime_ms = output.get("walltime_ms")
    if walltime_ms is None:
        walltime_ms = error.get("walltimeMs")
    cputime_ms = output.get("cputime_ms")
    if cputime_ms is None:
        cputime_ms = error.get("cputimeMs")
    memory_bytes = output.get("memory_bytes")
    if memory_bytes is None:
        memory_bytes = error.get("memoryBytes")

    with DB_LOCK:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO attack_result
                (tool, id, status, is_redos, prefix, infix, suffix, repeat_times, elapsed_ms, time, time_source, walltime_ms, cputime_ms, memory_bytes, full_json, logs_json, error_json, error_type, termination_reason, return_value, raw_output)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool_id,
                    regex_record["id"],
                    result.get("status", "failed"),
                    is_redos,
                    output.get("prefix", ""),
                    output.get("infix", ""),
                    output.get("suffix", ""),
                    output.get("repeat_times", -1),
                    elapsed_ms,
                    effective_time,
                    time_source,
                    walltime_ms,
                    cputime_ms,
                    memory_bytes,
                    json.dumps(output, ensure_ascii=False),
                    json.dumps(result.get("logs") or [], ensure_ascii=False),
                    json.dumps(error, ensure_ascii=False) if error else None,
                    error.get("type"),
                    error.get("terminationReason"),
                    error.get("returnValue"),
                    result.get("rawOutput")
                )
            )
            conn.execute("DELETE FROM attack_candidate WHERE tool = ? AND id = ?", (tool_id, regex_record["id"]))
            for candidate in candidates:
                attack = candidate.get("attack") if isinstance(candidate.get("attack"), dict) else {}
                attack_type = "fullText" if attack.get("fullText") else "pattern"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO attack_candidate
                    (tool, id, candidate_id, candidate_label, is_recommended, attack_type, full_text, prefix, infix, suffix, repeat_times, payload_length, preview, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tool_id,
                        regex_record["id"],
                        candidate.get("id"),
                        candidate.get("label"),
                        1 if candidate.get("id") == recommended_id else 0,
                        attack_type,
                        attack.get("fullText"),
                        attack.get("prefix"),
                        attack.get("infix"),
                        attack.get("suffix"),
                        attack.get("repeat_times", attack.get("repeatTimes")),
                        candidate.get("payloadLength"),
                        candidate.get("preview"),
                        json.dumps(candidate.get("metadata"), ensure_ascii=False) if candidate.get("metadata") is not None else None
                    )
                )
            conn.commit()
        finally:
            conn.close()


def process_task(db_path, regex_record, tool_id, args, tool_options, cpu_allocator):
    payload = {
        "regex": regex_record["regex"],
        "toolId": tool_id,
        "toolOptions": tool_options.get(tool_id) or {}
    }
    if args.timeout_seconds is not None:
        payload["timeoutSeconds"] = args.timeout_seconds
    if args.cpu_cores is not None:
        payload["cpuCores"] = args.cpu_cores
    if args.memory_mb is not None:
        payload["memoryMB"] = args.memory_mb
    allocated_cores = None
    if cpu_allocator and args.cpu_cores is not None:
        allocated_cores = cpu_allocator.acquire(args.cpu_cores)
        payload["cores"] = allocated_cores

    try:
        result = None
        for attempt in range(1, MAX_INFRA_RETRIES + 1):
            result = run_backend("run-tool", payload)
            if not retryable_infra_metrics_gap(result):
                break
            print_status(
                f"[Gen] regex={regex_record['id']} tool={tool_id} infra metrics missing; "
                f"retry {attempt}/{MAX_INFRA_RETRIES}"
            )
        if retryable_infra_metrics_gap(result):
            result = mark_inconclusive_infra(result, MAX_INFRA_RETRIES)
    finally:
        if cpu_allocator and allocated_cores:
            cpu_allocator.release(allocated_cores)

    write_attack_result(db_path, regex_record, tool_id, result)
    status = result.get("status", "failed")
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    print_status(
        f"[Gen] regex={regex_record['id']} tool={tool_id} status={status} is_redos={bool(output.get('is_redos') or output.get('candidates'))}"
    )
    return tool_id, regex_record["id"], result


def summarize(db_path):
    conn = sqlite3.connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM attack_result").fetchone()[0]
        redos = conn.execute("SELECT COUNT(*) FROM attack_result WHERE status = 'completed' AND is_redos = 1").fetchone()[0]
        failures = conn.execute("SELECT COUNT(*) FROM attack_result WHERE status = 'failed'").fetchone()[0]
        inconclusive = conn.execute("SELECT COUNT(*) FROM attack_result WHERE status = 'inconclusive'").fetchone()[0]
    finally:
        conn.close()
    print_status(f"[Gen] completed results={total} redos={redos} failures={failures} inconclusive={inconclusive}")


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        ensure_positive(args.workers, "workers")
        ensure_positive(args.timeout_seconds, "timeout-seconds")
        ensure_positive(args.cpu_cores, "cpu-cores")
        ensure_positive(args.memory_mb, "memory-mb")
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    visible_cpu_ids = detect_visible_cpu_ids()
    if args.cpu_cores is not None and args.cpu_cores > len(visible_cpu_ids):
        print(
            f"Requested {args.cpu_cores} CPU cores, but only {len(visible_cpu_ids)} are visible in this container.",
            file=sys.stderr
        )
        return 1

    try:
        meta = run_backend("meta")
        selected_tools, tool_map = normalize_selected_tools(meta, args.tools)
        tool_options = parse_tool_option_assignments(args.tool_option)
        validate_tool_options(tool_options, selected_tools, tool_map)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        regexes = load_regexes(str(input_path))
    except OSError as exc:
        print(f"Failed to read input file: {exc}", file=sys.stderr)
        return 1

    setup_database(args.output_db)
    insert_regexes(args.output_db, regexes)

    conn = sqlite3.connect(args.output_db)
    try:
        upsert_meta(conn, "schema_version", SCHEMA_VERSION)
        upsert_meta(conn, "gen_args", vars(args))
        upsert_meta(conn, "meta_snapshot", meta)
        upsert_meta(conn, "runtime_cpu_info", {
            "visibleCpuIds": visible_cpu_ids,
            "requestedCpuCores": args.cpu_cores
        })
        conn.commit()
    finally:
        conn.close()

    total_tasks = len(regexes) * len(selected_tools)
    if total_tasks == 0:
        print_status("[Gen] no regexes to process")
        return 0

    cpu_allocator = CpuAllocator(visible_cpu_ids) if args.cpu_cores is not None else None

    print_status(
        f"[Gen] regexes={len(regexes)} tools={len(selected_tools)} workers={args.workers} "
        f"visible_cpus={len(visible_cpu_ids)} requested_cpu_cores={args.cpu_cores or 'none'}"
    )

    failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_task, args.output_db, regex_record, tool_id, args, tool_options, cpu_allocator)
            for regex_record in regexes
            for tool_id in selected_tools
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failures += 1
                print_status(f"[Gen] task failed: {exc}")

    summarize(args.output_db)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
