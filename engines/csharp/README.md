# Benchmark Program - C#

This directory contains a C# implementation of the regex benchmark program using .NET 7.0 and the built-in System.Text.RegularExpressions library.

## Files

- `Benchmark.cs` - Main benchmark program
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

## Base64 Regex Examples

- `Y2F0` = "cat"
- `aGVsbG8gd29ybGQ=` = "hello world"
- `XGQr` = "\d+"
- `XGJjYXRcYg==` = "\bcat\b"
- `W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==` = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

## Directory Structure

```
csharp/
├── Benchmark.cs             # Main benchmark program
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
- **System.Text.RegularExpressions** - Built-in .NET regex library
- **Base64 support** - Built-in Convert.FromBase64String() method 