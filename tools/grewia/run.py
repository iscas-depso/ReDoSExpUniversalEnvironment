#!/usr/bin/env python3

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


DEFAULT_OPTIONS = {
    "regexEngine": "Java",
    "matchMode": 0,
    "attackStringLength": 100000,
    "candidateMode": "single",
    "decremental": False,
}

MATCH_MODE_TO_GREWIA = {
    0: "1",  # GREWIA uses 1 for partial match
    1: "0",  # GREWIA uses 0 for full match
}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
def parse_numeric_stem(file_path: Path) -> tuple[int, str]:
    stem = file_path.stem
    try:
        return (int(stem), file_path.name)
    except ValueError:
        return (sys.maxsize, file_path.name)


def read_json_if_exists(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_candidates(output_dir: Path) -> list[dict]:
    if not output_dir.exists():
        return []

    candidates = []
    for index, file_path in enumerate(sorted(output_dir.glob("*.txt"), key=parse_numeric_stem), start=1):
        try:
            attack_text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            attack_text = file_path.read_bytes().decode("utf-8", errors="replace")

        candidates.append(
            {
                "id": f"candidate-{index}",
                "label": f"Candidate {index}",
                "attack": {
                    "fullText": base64.b64encode(attack_text.encode("utf-8")).decode("ascii")
                },
                "preview": attack_text[:160],
                "payloadLength": len(attack_text),
                "metadata": {
                    "sourceFile": file_path.name,
                    "index": index,
                    "mode": "fullText",
                },
            }
        )

    return candidates


def normalize_elapsed_ms(value, fallback_ms: int) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback_ms


def normalize_repeat_times(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def load_options() -> dict:
    regex_engine = os.environ.get("GREWIA_REGEX_ENGINE", DEFAULT_OPTIONS["regexEngine"]).strip() or DEFAULT_OPTIONS["regexEngine"]
    try:
        match_mode = int(os.environ.get("GREWIA_MATCH_MODE", str(DEFAULT_OPTIONS["matchMode"])))
    except ValueError:
        match_mode = DEFAULT_OPTIONS["matchMode"]
    if match_mode not in (0, 1):
        match_mode = DEFAULT_OPTIONS["matchMode"]

    try:
        attack_string_length = int(os.environ.get("GREWIA_ATTACK_STRING_LENGTH", str(DEFAULT_OPTIONS["attackStringLength"])))
    except ValueError:
        attack_string_length = DEFAULT_OPTIONS["attackStringLength"]
    if attack_string_length < 64:
        attack_string_length = 64

    candidate_mode = os.environ.get("GREWIA_CANDIDATE_MODE", DEFAULT_OPTIONS["candidateMode"]).strip().lower()
    if candidate_mode not in {"single", "multiple"}:
        candidate_mode = DEFAULT_OPTIONS["candidateMode"]

    return {
        "regexEngine": regex_engine,
        "matchMode": match_mode,
        "attackStringLength": attack_string_length,
        "candidateMode": candidate_mode,
        "decremental": env_bool("GREWIA_DECREMENTAL", DEFAULT_OPTIONS["decremental"]),
    }


def build_result(raw_result: dict, candidates: list[dict], normalized_options: dict, fallback_elapsed_ms: int) -> dict:
    is_redos = bool(raw_result.get("is_redos")) or bool(candidates)
    result = {
        "elapsed_ms": normalize_elapsed_ms(raw_result.get("elapsed_ms"), fallback_elapsed_ms),
        "is_redos": is_redos,
        "prefix": raw_result.get("prefix", "") if is_redos else "",
        "infix": raw_result.get("infix", "") if is_redos else "",
        "suffix": raw_result.get("suffix", "") if is_redos else "",
        "repeat_times": normalize_repeat_times(raw_result.get("repeat_times", -1)) if is_redos else -1,
        "recommendedCandidateId": candidates[0]["id"] if candidates else None,
        "candidates": candidates,
        "toolMeta": {
            "normalizedOptions": normalized_options,
            "candidateCount": len(candidates),
        },
    }
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 run.py <base64_regex> <output_json_file>", file=sys.stderr)
        return 1

    base64_regex = sys.argv[1]
    output_json_file = Path(sys.argv[2])
    output_json_file.parent.mkdir(parents=True, exist_ok=True)

    tool_dir = Path(__file__).resolve().parent
    grewia_exe = tool_dir / "build" / "GREWIA"
    if not grewia_exe.exists():
        print(f"GREWIA executable not found at {grewia_exe}", file=sys.stderr)
        return 1

    normalized_options = load_options()
    temp_root = Path(tempfile.mkdtemp(prefix="grewia-run-"))
    output_dir = temp_root / "candidates"
    raw_output_path = temp_root / "grewia-output.json"

    cmd = [
        str(grewia_exe),
        base64_regex,
        str(raw_output_path),
        str(output_dir),
        str(normalized_options["attackStringLength"]),
        "1" if normalized_options["candidateMode"] == "single" else "0",
        "1" if normalized_options["decremental"] else "0",
        MATCH_MODE_TO_GREWIA[normalized_options["matchMode"]],
        normalized_options["regexEngine"],
    ]

    start_time = time.time()
    try:
        process = subprocess.run(
            cmd,
            cwd=tool_dir,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        elapsed_ms = int((time.time() - start_time) * 1000)

        if process.stdout:
            sys.stdout.write(process.stdout)
        if process.stderr:
            sys.stderr.write(process.stderr)

        raw_result = read_json_if_exists(raw_output_path)
        candidates = read_candidates(output_dir)

        if process.returncode != 0 and not raw_result and not candidates:
            print(f"GREWIA failed with exit code {process.returncode}", file=sys.stderr)
            return process.returncode or 1

        result = build_result(raw_result, candidates, normalized_options, elapsed_ms)
        output_json_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0
    except subprocess.TimeoutExpired:
        print("GREWIA execution timed out after 300 seconds", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
