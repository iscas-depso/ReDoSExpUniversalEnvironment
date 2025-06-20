# Benchmark Program - Java 8

## Files
- `Benchmark.java` - Main benchmark program using traditional Java 8 features
- `Makefile` - Build configuration with Java 8 specific settings and environment isolation
- `bin/benchmark` - Executable wrapper script enforcing Java 8 environment (created after building)
- `bin/Benchmark.class` - Compiled Java bytecode targeting Java 8 (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## Building and Running

### Build the program
```bash
# Build the Java 8 benchmark program (automatically checks Java 8 availability)
make all

# Check Java 8 version
make java-version

# Alternative: build directly with javac (requires Java 8)
mkdir -p bin
/usr/lib/jvm/java-8-openjdk-amd64/bin/javac -d bin -source 8 -target 8 Benchmark.java
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

## Environment Isolation

This implementation is completely isolated from other Java versions:

- **Dedicated JAVA_HOME**: Uses `/usr/lib/jvm/java-8-openjdk-amd64`
- **Version-specific Compilation**: `-source 8 -target 8` flags ensure Java 8 compliance
- **Isolated Execution**: Wrapper script enforces Java 8 runtime
- **No Interference**: Completely separate from `java11` implementation

## Java 8 Features Used

This implementation uses traditional Java 8 features:

- **Traditional Type Declarations**: Explicit type declarations for clarity
- **Classic File I/O**: `Files.readAllBytes()` for file reading
- **System Timing**: `System.nanoTime()` for high-precision timing
- **Standard Exception Handling**: Traditional try-catch blocks
- **Mature JVM Performance**: Stable and well-optimized runtime

## Requirements

- **Java**: JDK 8 (specifically targets Java 8)
- **Make**: For build automation (optional)
- **Environment**: Isolated from other Java versions

## Directory Structure

```
java8/
├── Benchmark.java        # Main benchmark program (Java 8 features)
├── Makefile             # Build configuration (Java 8 specific)
├── README.md            # This documentation
├── bin/                 # Compiled executables (created during build)
│   ├── benchmark        # Executable wrapper script (Java 8 enforced)
│   └── Benchmark.class  # Compiled Java 8 bytecode
└── tests/               # Test suite
    ├── run_tests.sh     # Comprehensive test runner
    ├── simple_test.sh   # Simple test script
    ├── test_data.txt    # Comprehensive test data
    ├── simple_test.txt  # Simple test data
    └── full_match_test.txt # Full match test data
``` 