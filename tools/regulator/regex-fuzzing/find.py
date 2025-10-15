import subprocess
import sys

def main():
    with open(sys.argv[1], "r") as f:
        lines = [line.strip() for line in f if line.strip() != ""]
        print(f"{len(lines)} regexes")
        lines = set(lines)
        print(f"{len(lines)} unique regexes")
        for line in lines:
            print(line)
            result = subprocess.run(["grep", "-RnwF", *sys.argv[2:], "-e", line.strip()], stdout=subprocess.PIPE)
            print(
                "\n".join([
                    f"    {l}" for l in result.stdout.decode("utf-8").strip().split("\n")
                ]),
                end="\n"
            )

main()
