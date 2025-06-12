# Benchmark Program - Rust

## Files
- `src/main.rs` - Main Rust benchmark program source code
- `Cargo.toml` - Rust project configuration and dependencies
- `Cargo.lock` - Dependency lock file
- `Makefile` - Build configuration and commands
- `bin/benchmark` - Compiled Rust binary (created by make)
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

# Build the program
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
./bin/benchmark <base64_regex> <filename> <match_mode>
```

- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to the file containing text to match
- `match_mode`: 1 for full match, 0 for partial match

### Examples

```bash
# Count occurrences of "cat" (partial match)
./bin/benchmark "Y2F0" "tests/simple_test.txt" "0"

# Full match test with "hello world"
./bin/benchmark "aGVsbG8gd29ybGQ=" "tests/full_match_test.txt" "1"

# Email pattern matching
./bin/benchmark "W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==" "tests/test_data.txt" "0"
```

## Directory Structure

```
rust/
├── src/
│   └── main.rs               # Main Rust program source
├── Cargo.toml                # Rust project configuration
├── Cargo.lock                # Dependency lock file
├── Makefile                  # Build configuration
├── README.md                 # This documentation
├── bin/                      # Executable directory
│   └── benchmark            # Compiled Rust binary
├── target/                   # Cargo build directory
└── tests/                    # Test suite directory
    ├── run_tests.sh         # Comprehensive test runner
    ├── simple_test.sh       # Simple test script
    ├── test_data.txt        # Comprehensive test data
    ├── simple_test.txt      # Simple test data
    └── full_match_test.txt  # Full match test data
``` 