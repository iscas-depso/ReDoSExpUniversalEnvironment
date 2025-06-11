# Benchmark Program - Java

## Files
- `Benchmark.java` - Main benchmark program with base64 regex support and dual matching modes
- `Makefile` - Build configuration with targets for compilation, testing, and cleanup
- `bin/benchmark` - Executable wrapper script (created after building)
- `bin/Benchmark.class` - Compiled Java bytecode (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## Building and Running

### Build the program
```bash
# Build the benchmark program
make all

# Alternative: build directly with javac
mkdir -p bin
javac -d bin Benchmark.java
```

### Run tests
```bash
# Run comprehensive test suite
make test

# Run simple test for quick validation
make simple-test

# Alternative: run tests directly
cd tests && ./run_tests.sh
cd tests && ./simple_test.sh
```

## Program Usage

The program accepts exactly three command-line arguments:

```bash
./bin/benchmark <base64_regex> <filename> <match_mode>
```

**Parameters:**
- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to the file containing text to match
- `match_mode`: 1 for full match, 0 for partial match

**Output Format:**
```
{elapsed_time} - {match_count}
```

**Examples:**

1. **Partial matching** (find all matches):
```bash
# Search for "cat" in simple_test.txt
./bin/benchmark Y2F0 tests/simple_test.txt 0
# Output example: 2.567800 - 5

# Search for email patterns in test_data.txt
./bin/benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== tests/test_data.txt 0
```

2. **Full matching** (entire text must match):
```bash
# Check if entire file matches "hello world"
./bin/benchmark aGVsbG8gd29ybGQ= tests/full_match_test.txt 1
# Output example: 1.234500 - 1

# Check if entire file matches "hello" (should fail)
./bin/benchmark aGVsbG8= tests/full_match_test.txt 1
# Output example: 0.987600 - 0
```

**Common Base64 Regex Patterns:**
- `cat` → `Y2F0`
- `hello` → `aGVsbG8=`
- `\d+` → `XGQr`
- `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` → `W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==`

## Program Features

- **Base64 Decoding**: Uses Java's built-in `Base64` decoder for reliable base64 processing
- **Dual Match Modes**: Supports both partial matching (`find()`) and full matching (`matches()`)
- **High Precision Timing**: Uses `System.nanoTime()` for microsecond-level timing accuracy
- **Robust Error Handling**: Comprehensive error checking for file I/O, regex compilation, and argument validation
- **Cross-Platform Compatibility**: Works on any platform with Java 8+ installed

## Requirements

- **Java**: JDK 8 or higher
- **Make**: For build automation (optional)

## Directory Structure

```
java/
├── Benchmark.java        # Main benchmark program
├── Makefile             # Build configuration
├── README.md            # This documentation
├── bin/                 # Compiled executables (created during build)
│   ├── benchmark        # Executable wrapper script (created during build)
│   └── Benchmark.class  # Compiled Java bytecode (created during build)
└── tests/               # Test suite
    ├── run_tests.sh     # Comprehensive test runner
    ├── simple_test.sh   # Simple test script
    ├── test_data.txt    # Comprehensive test data
    ├── simple_test.txt  # Simple test data
    └── full_match_test.txt # Full match test data
``` 