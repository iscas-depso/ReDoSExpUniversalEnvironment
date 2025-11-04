#!/usr/bin/env python3
import argparse
import multiprocessing as mp
import os
import time


def cpus_allowed_list():
    try:
        with open("/proc/self/status", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("Cpus_allowed_list:"):
                    return line.strip()
    except Exception:
        pass
    return "Cpus_allowed_list: unknown"


def work(n: int) -> int:
    x = 0
    for _ in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
    return x


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--loops", type=int, default=15000000)
    p.add_argument("--workers", type=int, default=2)
    args = p.parse_args()

    print(cpus_allowed_list(), flush=True)
    print(f"workers={args.workers} loops_per_worker={args.loops}")
    t0 = time.time()
    with mp.Pool(args.workers) as pool:
        r = pool.map(work, [args.loops] * args.workers)
    t1 = time.time()
    print(f"result={sum(r)} elapsed={t1 - t0:.3f}s", flush=True)


if __name__ == "__main__":
    main()

