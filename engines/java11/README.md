# Benchmark Program - Java 11

## Files
- `Benchmark.java` - Main benchmark program using Java 11 features (var, Path.of, Files.readString)
- `Makefile` - Build configuration with Java 11 specific settings and environment isolation
- `bin/benchmark` - Executable wrapper script enforcing Java 11 environment (created after building)
- `bin/Benchmark.class` - Compiled Java bytecode targeting Java 11 (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## Java 11 Features Used

This implementation showcases modern Java 11 features:

- **Local Variable Type Inference (`var`)**: Reduces boilerplate code
- **Enhanced File I/O (`Path.of`, `Files.readString`)**: Simplified file operations
- **Modern Time API (`Instant`, `Duration`)**: High-precision timing
- **Improved String Handling**: Better performance with modern JVM optimizations
- **Enhanced Exception Handling**: Cleaner error management

## Building and Running

### Build the program
```bash
# Build the Java 11 benchmark program (automatically checks Java 11 availability)
make all

# Check Java 11 version
make java-version

# Alternative: build directly with javac (requires Java 11)
mkdir -p bin
/usr/lib/jvm/java-11-openjdk-amd64/bin/javac -d bin --release 11 Benchmark.java
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

## Environment Isolation

This implementation is completely isolated from other Java versions:

- **Dedicated JAVA_HOME**: Uses `/usr/lib/jvm/java-11-openjdk-amd64`
- **Version-specific Compilation**: `--release 11` flag ensures Java 11 compliance
- **Isolated Execution**: Wrapper script enforces Java 11 runtime
- **No Interference**: Completely separate from `java8` implementation

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
# Output example: 1.234567 - 5

# Search for email patterns in test_data.txt
./bin/benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== tests/test_data.txt 0
```

2. **Full matching** (entire text must match):
```bash
# Check if entire file matches "hello world"
./bin/benchmark aGVsbG8gd29ybGQ= tests/full_match_test.txt 1
# Output example: 0.987654 - 1

# Check if entire file matches "hello" (should fail)
./bin/benchmark aGVsbG8= tests/full_match_test.txt 1
# Output example: 0.876543 - 0
```

## Performance Characteristics

Java 11 provides several performance improvements over Java 8:

- **Enhanced Garbage Collection**: Lower pause times with G1GC improvements
- **Better JIT Compilation**: More aggressive optimizations
- **Improved String Performance**: Compact strings and better memory usage
- **Modern JVM Optimizations**: Better CPU utilization and caching

## Requirements

- **Java**: JDK 11 or higher (specifically targets Java 11)
- **Make**: For build automation (optional)
- **Environment**: Isolated from other Java versions

## Directory Structure

```
java11/
├── Benchmark.java        # Main benchmark program (Java 11 features)
├── Makefile             # Build configuration (Java 11 specific)
├── README.md            # This documentation
├── bin/                 # Compiled executables (created during build)
│   ├── benchmark        # Executable wrapper script (Java 11 enforced)
│   └── Benchmark.class  # Compiled Java 11 bytecode
└── tests/               # Test suite
    ├── run_tests.sh     # Comprehensive test runner
    ├── simple_test.sh   # Simple test script
    ├── test_data.txt    # Comprehensive test data
    ├── simple_test.txt  # Simple test data
    └── full_match_test.txt # Full match test data
```

## Comparison with Java 8 Implementation

| Feature | Java 8 | Java 11 |
|---------|---------|---------|
| Type Inference | Manual types | `var` keyword |
| File I/O | `Files.readAllBytes()` | `Files.readString()` |
| Time API | `System.nanoTime()` | `Instant`/`Duration` |
| String Handling | Traditional | Compact strings |
| Performance | Good | Enhanced |
| Memory Usage | Higher | Optimized |

This implementation demonstrates the evolution of Java while maintaining complete compatibility with the project's interface standards. 