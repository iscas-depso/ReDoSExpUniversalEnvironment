import multiprocessing.pool
import pathlib
import subprocess
import sys

fuzzer_path = "/opt/regulator-dynamic/fuzzer/build/fuzzer"
driver_path = "/opt/regulator-dynamic/driver/main.py"

def worker(arg):
    regex, flags = arg
    print("starting", regex, flags, flush=True)
    args = ["python", driver_path, "--regex", regex, "--flags", flags, "-v", "--fuzzer-binary", fuzzer_path]
    # print(args, flush=True)
    result = subprocess.run(
        args,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )
    print(f"{'=' * 20} testing /{regex}/{flags} {'=' * 20}", flush=True)
    print(result.stdout.decode("utf-8"), flush=True)

def main():
    regexes = []
    with open(sys.argv[1], "r") as f:
        lines = [line.strip() for line in f if line.strip() != ""]
        print(f"{len(lines)} regexes")
        lines = set(lines)
        print(f"{len(lines)} unique regexes")
        for line in lines:
            flags = line[line.rindex("/") + 1:]
            line = line.rstrip("gmis")
            # just some sanity checks
            assert line.endswith("/")
            assert line.startswith("/")
            assert not line.endswith("//")
            assert not line.startswith("//")
            line = line.strip("/")
            regexes.append((line, flags))

    with multiprocessing.pool.ThreadPool(multiprocessing.cpu_count()) as pool:
        pool.map(worker, regexes)

main()
