# Benchmark Program – AWK

## Files
- `benchmark.awk` - Main AWK benchmark script (uses system base64 command)
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

## Directory Structure
```
awk/
├── benchmark.awk
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