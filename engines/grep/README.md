# Benchmark Program – Grep

## Files
- `benchmark.sh` - Main bash wrapper script for grep benchmarking
- `Makefile` - Build configuration
- `tests/` - Test files and scripts

## Building and Running
### Build
```bash
make all
```

### Run tests
```bash
make test        # Run all tests
make simple-test # Run simple tests only
```

## Program Usage
```bash
./bin/benchmark <base64_regex> <filename> <match_mode>
```

Example:
```bash
./bin/benchmark Y2F0 tests/simple_test.txt 0
```

Notes:
- The wrapper now reads payload bytes directly from the input file instead of round-tripping through shell variables, so embedded `NUL` and control bytes are preserved in partial-match mode.
- GNU `grep` full-match mode still cannot represent an entire payload as a single record when the payload itself contains `NUL` bytes. In that case the wrapper exits with a clear error instead of silently mutating the payload.

## Directory Structure
```
grep/
├── benchmark.sh
├── Makefile
├── README.md
├── tests/
│   ├── run_tests.sh
│   ├── simple_test.sh
│   ├── test_data.txt
│   ├── simple_test.txt
│   └── full_match_test.txt
└── bin/ (created by build)
``` 
