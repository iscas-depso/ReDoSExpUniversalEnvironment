# Benchmark Program

This directory contains a C program that benchmarks regex performance with a comprehensive test suite.

## Files

- `benchmark.c` - Main benchmark program
- `Makefile` - Build configuration
- `bin/` - Directory containing compiled binaries
- `tests/` - Test suite directory containing:
  - `run_tests.sh` - Test runner script
  - `simple_test.sh` - Simple test script
  - `test_data.txt` - Test file with various text patterns
  - `simple_test.txt` - Simple test file for basic matching
  - `full_match_test.txt` - Test file for full match scenarios

## Building and Running

### Build the program
```bash
# Build the program (outputs to bin/ directory)
make all

# Run comprehensive tests
make test

# Run simple tests
make simple-test

# Clean up build artifacts
make clean
```

## Program Usage

```bash
./bin/benchmark <base64_regex> <filename> <match_mode>
```

### Parameters:
- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to file containing text to match
- `match_mode`: 
  - `1` for full match (entire text must match regex)
  - `0` for partial match (find all matches in text)

### Output Format:
```
{elapsed_time} - {match_count}
```
- `elapsed_time`: Execution time in milliseconds
- `match_count`: Number of matches found

## Test Cases

The test suite includes:

1. **Simple word match**: Tests basic pattern matching with "cat"
2. **Email pattern match**: Tests complex regex for email addresses
3. **Digit pattern match**: Tests digit pattern matching
4. **Full match test**: Tests full text matching
5. **Full match failure**: Tests when full match should fail
6. **Word boundary test**: Tests word boundary regex

## Base64 Regex Examples

- `Y2F0` = "cat"
- `aGVsbG8gd29ybGQ=` = "hello world"
- `XGQr` = "\d+"
- `XGJjYXRcYg==` = "\bcat\b"
- `W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==` = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

## Directory Structure

```
c/
├── benchmark.c              # Main benchmark program
├── Makefile                 # Build configuration
├── README.md               # This file
├── bin/                    # Compiled binaries
│   └── benchmark           # Compiled program (after 'make all')
└── tests/                  # Test suite
    ├── run_tests.sh        # Comprehensive test runner
    ├── simple_test.sh      # Simple test script
    ├── test_data.txt       # Comprehensive test data
    ├── simple_test.txt     # Simple test data
    └── full_match_test.txt # Full match test data
```

## Dependencies

- **libpcre2-dev**: PCRE2 library for regex support
- **libssl-dev**: OpenSSL library for Base64 decoding
- **build-essential**: GCC compiler and build tools 