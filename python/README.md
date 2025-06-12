# Benchmark Program - Python

## Files
- `benchmark.py` - Main Python benchmark program
- `Makefile` - Build configuration and commands
- `bin/benchmark` - Executable Python script (created by make)
- `tests/run_tests.sh` - Comprehensive test runner script
- `tests/simple_test.sh` - Simple test script
- `tests/test_data.txt` - Comprehensive test data
- `tests/simple_test.txt` - Simple test data
- `tests/full_match_test.txt` - Full match test data

## Building and Running

### Build the program
```bash
# Install dependencies (if needed)
make install-deps

# Prepare the program
make all
```

### Run tests
```bash
# Run all tests
make test

# Run simple test only
make simple-test
```

## Program Usage

The benchmark program accepts three command-line arguments:

```bash
python3 benchmark.py <base64_regex> <filename> <match_mode>
```

- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to the file containing text to match
- `match_mode`: 1 for full match, 0 for partial match

### Examples

```bash
# Count occurrences of "cat" (partial match)
python3 benchmark.py "Y2F0" "tests/simple_test.txt" "0"

# Full match test with "hello world"
python3 benchmark.py "aGVsbG8gd29ybGQ=" "tests/full_match_test.txt" "1"

# Email pattern matching
python3 benchmark.py "W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==" "tests/test_data.txt" "0"
```

## Directory Structure

```
python/
├── benchmark.py              # Main Python program
├── Makefile                  # Build configuration
├── README.md                 # This documentation
├── bin/                      # Executable directory
│   └── benchmark            # Python script executable
└── tests/                    # Test suite directory
    ├── run_tests.sh         # Comprehensive test runner
    ├── simple_test.sh       # Simple test script
    ├── test_data.txt        # Comprehensive test data
    ├── simple_test.txt      # Simple test data
    └── full_match_test.txt  # Full match test data
``` 