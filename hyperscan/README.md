# Benchmark Program – Hyperscan

## Files
- `benchmark.cpp` - Main benchmark program using Hyperscan library
- `Makefile` - Build configuration
- `tests/` - Test scripts and data files

## Building and Running
### Build
```bash
make
```

### Run tests
```bash
cd tests
./run_tests.sh
```

## Program Usage
```bash
./bin/benchmark <base64_regex> <filename> <match_mode>
```

Example:
```bash
./bin/benchmark "XGFiYw==" test_data.txt 0
```

Where:
- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to text file to search
- `match_mode`: 0 for partial match, 1 for full match

## Directory Structure
```
hyperscan/
├── benchmark.cpp
├── Makefile
├── README.md
├── tests/
│   ├── run_tests.sh
│   ├── simple_test.sh
│   ├── test_data.txt
│   ├── simple_test.txt
│   └── full_match_test.txt
└── bin/ (created by build)
    └── benchmark
```
