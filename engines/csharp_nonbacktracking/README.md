# Benchmark Program - C# (Non-Backtracking)

This directory contains a C# implementation of the regex benchmark program using .NET 7.0 and the **non-backtracking regex engine** (`RegexOptions.NonBacktracking`).

## Key Feature

This implementation uses .NET's **non-backtracking regex engine**, which provides:
- **Predictable performance**: O(n) time complexity regardless of regex complexity
- **No catastrophic backtracking**: Protection against ReDoS (Regular expression Denial of Service) attacks
- **Memory efficiency**: Lower memory usage for complex patterns
- **Consistent timing**: More reliable benchmarking results

## Files

- `Benchmark.cs` - Main benchmark program (using `RegexOptions.NonBacktracking`)
- `benchmark.csproj` - Project configuration file
- `Makefile` - Build configuration (using dotnet CLI)
- `bin/` - Directory containing compiled binaries
- `obj/` - Directory containing build artifacts
- `tests/` - Test suite directory containing:
  - `run_tests.sh` - Test runner script
  - `simple_test.sh` - Simple test script
  - `test_data.txt` - Test file with various text patterns
  - `simple_test.txt` - Simple test file for basic matching
  - `full_match_test.txt` - Test file for full match scenarios

## Building and Running

### Build the program
```bash
# Restore dependencies and build the program
make all

# Alternative: use dotnet CLI directly
dotnet build -c Release

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
- `elapsed_time`: Execution time in milliseconds (6 decimal places)
- `match_count`: Number of matches found

## Test Cases

The test suite includes:

1. **Simple word match**: Tests basic pattern matching with "cat"
2. **Email pattern match**: Tests complex regex for email addresses
3. **Digit pattern match**: Tests digit pattern matching
4. **Full match test**: Tests full text matching
5. **Full match failure**: Tests when full match should fail
6. **Word boundary test**: Tests word boundary regex

## Non-Backtracking Engine Benefits

Compared to the traditional backtracking regex engine, this implementation:

- **Provides consistent performance**: No exponential time complexity scenarios
- **Prevents ReDoS attacks**: Safe against malicious input patterns
- **Uses less memory**: More efficient memory usage for complex patterns
- **Offers predictable timing**: Better for benchmarking and performance testing

## Base64 Regex Examples

- `Y2F0` = "cat"
- `aGVsbG8gd29ybGQ=` = "hello world"
- `XGQr` = "\d+"
- `XGJjYXRcYg==` = "\bcat\b"
- `W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==` = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

## Directory Structure

```
csharp_nonbacktracking/
├── Benchmark.cs             # Main benchmark program (non-backtracking)
├── benchmark.csproj         # .NET project configuration
├── Makefile                 # Build configuration
├── README.md               # This file
├── bin/                    # Compiled binaries
│   └── benchmark           # Compiled program (after 'make all')
├── obj/                    # Build artifacts
└── tests/                  # Test suite
    ├── run_tests.sh        # Comprehensive test runner
    ├── simple_test.sh      # Simple test script
    ├── test_data.txt       # Comprehensive test data
    ├── simple_test.txt     # Simple test data
    └── full_match_test.txt # Full match test data
```

## Dependencies

- **.NET 7.0 SDK** - Required for compilation and execution
- **System.Text.RegularExpressions** - Built-in .NET regex library with non-backtracking support
- **Base64 support** - Built-in Convert.FromBase64String() method

## Performance Characteristics

This non-backtracking implementation typically shows:
- **More consistent timing** across different input patterns
- **Better worst-case performance** for complex regex patterns
- **Slightly higher baseline overhead** for simple patterns
- **Excellent scalability** with input size and pattern complexity 