# Regex fuzzing driver

This is a driver script that invokes https://github.com/ucsb-seclab/regulator-dynamic to fuzz a regular expression for
ReDoS vulnerabilities. More info at https://www.usenix.org/system/files/sec22summer_mclaughlin.pdf.

## Instructions

`make run` will build and run a container using `podman`. It will take a while.

After that, you can fuzz regular expressions with:
```
python3 main.py --fuzzer-binary /opt/regulator-dynamic/fuzzer/build/fuzzer -v --regex "http://(b|[b])*c" --flags ""
```

This repo provides a parallel runner script that takes a file of js regexes with one `/pattern/flags` per line
```
python3 runner.py regexes.txt
```
