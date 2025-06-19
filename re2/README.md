# Benchmark Program – RE2

## Files
- `src/benchmark.cpp` - Main benchmark program using RE2 engine
- `Makefile` - Build configuration
- `tests/` - Test scripts and data files

## Building and Running
### Build
```bash
make all
```

### Run tests
```bash
make test
```

## Program Usage
```bash
./bin/benchmark <base64_regex> <filename> <match_mode>
```

Example:
```bash
./bin/benchmark "Y2F0" "tests/simple_test.txt" "0"
```

## Directory Structure
```
re2/
├── src/
│   └── benchmark.cpp
├── tests/
│   ├── run_tests.sh
│   ├── simple_test.sh
│   ├── test_data.txt
│   ├── simple_test.txt
│   └── full_match_test.txt
├── Makefile
├── README.md
└── bin/ (created by build)
``` 