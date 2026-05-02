#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - Regulator
Entry point script that follows the project contract.
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 600
TIMEOUT_EXIT_CODE = 124

witness_pat = re.compile(r'SUMMARY.+? word="(.+?)" Total=(\d+) MaxObservation')
max_tot_exceeded_pat = re.compile(r'Maximum Total reached:.*?word="(.+?)" Total=(\d+) MaxObservation')


def load_timeout_seconds():
    try:
        timeout_seconds = int(os.environ.get("TOOL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout_seconds if timeout_seconds > 0 else DEFAULT_TIMEOUT_SECONDS


def build_failure(elapsed_ms, error_type, message, **extra):
    error = {
        "type": error_type,
        "message": message,
    }
    for key, value in extra.items():
        if value is not None:
            error[key] = value
    return {
        "elapsed_ms": elapsed_ms,
        "is_redos": False,
        "prefix": "",
        "infix": "",
        "suffix": "",
        "repeat_times": -1,
        "error": error,
    }


def decode_witness_one_byte(text):
    import ast
    escaped = text.replace("'", "\\'")
    return ast.literal_eval("b'" + escaped + "'")


async def run_fuzzer(fuzzer_binary, regex_b64, flags, ftime_ms=240000, length=200, width=1):
    witness = None
    witness_score = 0
    timed_out = False

    fuzz_deadline = time.time() + ftime_ms / 1000
    current_length = length
    maxtot = 500_000
    n_backoffs = 0

    fuzzer_flags = []
    if flags.strip():
        fuzzer_flags += ["--flags", flags.strip()]

    while True:
        process = await asyncio.create_subprocess_exec(
            fuzzer_binary,
            "--bregexp", regex_b64,
            "--lengths", str(current_length),
            "--widths", str(width),
            "--timeout", str(int(ftime_ms / 1000) + 30),
            "--maxtot", str(maxtot),
            *fuzzer_flags,
            stderr=asyncio.subprocess.STDOUT,
            stdout=asyncio.subprocess.PIPE,
        )

        my_witness = None
        my_witness_score = 0
        while True:
            time_remaining = fuzz_deadline - time.time()
            if time_remaining <= 0:
                timed_out = True
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), 10)
                except asyncio.TimeoutError:
                    process.kill()
                break

            try:
                line = await asyncio.wait_for(process.stdout.readline(), time_remaining)
            except asyncio.TimeoutError:
                continue

            if line is None or len(line) == 0:
                break

            decoded = line.decode("utf8")
            tot_exceed_mat = max_tot_exceeded_pat.search(decoded)
            if tot_exceed_mat is not None:
                try:
                    await asyncio.wait_for(process.wait(), 10)
                except asyncio.TimeoutError as error:
                    raise RuntimeError("Regulator fuzzer exceeded shutdown time") from error
                my_witness = tot_exceed_mat.group(1)
                my_witness_score = int(tot_exceed_mat.group(2))
                break

            witness_mat = witness_pat.search(decoded)
            if witness_mat is not None:
                my_witness = witness_mat.group(1)
                my_witness_score = int(witness_mat.group(2))

        if n_backoffs == 0 or my_witness_score >= maxtot * 0.60:
            witness = my_witness
            witness_score = my_witness_score

        time_remaining = fuzz_deadline - time.time()
        if timed_out:
            break
        if time_remaining > 5 and witness_score >= maxtot * 0.95:
            old_len = current_length
            current_length = (current_length - 20) // 2 + 20
            if current_length == old_len:
                break
            n_backoffs += 1
        else:
            break

    return witness, witness_score, timed_out


def load_regulator_modules(script_dir):
    driver_dir = str(script_dir / "regulator-dynamic" / "driver")
    if driver_dir in sys.path:
        sys.path.remove(driver_dir)
    sys.path.insert(0, driver_dir)
    import pump  # type: ignore
    import binsearch_pump  # type: ignore
    return pump, binsearch_pump


def main():
    start_time = time.time()
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)

    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]
    timeout_seconds = load_timeout_seconds()
    total_timeout_ms = timeout_seconds * 1000

    script_dir = Path(__file__).parent
    fuzzer_binary = script_dir / "regulator-dynamic" / "fuzzer" / "build" / "fuzzer"

    try:
        if not fuzzer_binary.exists():
            raise FileNotFoundError(f"Regulator fuzzer not found at {fuzzer_binary}")

        regex_bytes = base64.b64decode(base64_regex, validate=True)
        pump, _binsearch = load_regulator_modules(script_dir)
        pump.fuzzer_binary = str(fuzzer_binary)

        witness, witness_score, timed_out = asyncio.run(run_fuzzer(
            str(fuzzer_binary),
            base64_regex,
            "",
            ftime_ms=total_timeout_ms,
            length=200,
            width=1
        ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        if timed_out:
            output_json = build_failure(
                elapsed_ms,
                "timeout",
                f"Regulator timed out after {timeout_seconds} seconds.",
                returnValue=TIMEOUT_EXIT_CODE,
            )
            exit_code = TIMEOUT_EXIT_CODE
        else:
            output_json = {
                "elapsed_ms": elapsed_ms,
                "is_redos": False,
                "prefix": "",
                "infix": "",
                "suffix": "",
                "repeat_times": -1,
            }
            exit_code = 0

            if witness and witness_score > 0:
                bwitness = decode_witness_one_byte(witness)
                remaining_ms = max(0, total_timeout_ms - elapsed_ms)
                deadline = time.time() * 1000 + remaining_ms
                report = pump.get_pump_report(regex_bytes, b"", bwitness, 1, deadline)
                report_class = report.get("class", "UNKNOWN")
                repeat_times = -1
                if report_class.startswith("EXPONENTIAL"):
                    repeat_times = 100000
                elif report_class == "POLYNOMIAL":
                    repeat_times = 100000

                if repeat_times > 0 and "pump_pos" in report and "pump_len" in report:
                    pump_pos = report["pump_pos"]
                    pump_len = report["pump_len"]
                    prefix = bwitness[:pump_pos]
                    infix = bwitness[pump_pos:pump_pos + pump_len]
                    suffix = bwitness[pump_pos + pump_len:]
                    output_json.update({
                        "is_redos": True,
                        "prefix": base64.b64encode(prefix).decode("utf-8"),
                        "infix": base64.b64encode(infix).decode("utf-8"),
                        "suffix": base64.b64encode(suffix).decode("utf-8"),
                        "repeat_times": repeat_times
                    })
                elif repeat_times > 0:
                    output_json.update({
                        "is_redos": True,
                        "prefix": base64.b64encode(b"").decode("utf-8"),
                        "infix": base64.b64encode(bwitness).decode("utf-8"),
                        "suffix": base64.b64encode(b"").decode("utf-8"),
                        "repeat_times": repeat_times
                    })
    except Exception as error:
        output_json = build_failure(
            int((time.time() - start_time) * 1000),
            "tool_exception",
            str(error),
        )
        exit_code = 1

    output_json["elapsed_ms"] = int((time.time() - start_time) * 1000)
    with open(output_file_path, "w", encoding="utf-8") as handle:
        json.dump(output_json, handle, indent=2)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
