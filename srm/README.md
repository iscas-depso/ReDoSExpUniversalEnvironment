# Benchmark Program - SRM C#

## Files

- `Benchmark.cs` - Main program source code using Microsoft.Automata.SRM
- `benchmark.csproj` - .NET project configuration file with SRM dependency
- `Makefile` - Build and test automation
- `README.md` - This documentation file
- `tests/` - Test suite directory
  - `run_tests.sh` - Comprehensive test runner script
  - `simple_test.sh` - Simple test script
  - `test_data.txt` - Comprehensive test data
  - `simple_test.txt` - Simple test data
  - `full_match_test.txt` - Full match test data

## Building and Running

### Build the program

```bash
# Build using Makefile
make build

# Or build directly with dotnet
dotnet restore
dotnet build
```

### Run tests

```bash
# Run comprehensive tests
make test

# Run simple tests
make simple-test

# Or run tests directly
cd tests
./run_tests.sh
./simple_test.sh
```

## Program Usage

The program accepts three command-line arguments:

```bash
# Using the executable script
./bin/benchmark <base64_regex> <filename> <match_mode>

# Or using dotnet run directly
dotnet run -- <base64_regex> <filename> <match_mode>
```

**Parameters:**
- `base64_regex`: Base64-encoded regular expression
- `filename`: Path to file containing text to match
- `match_mode`: 0 for partial match, 1 for full match

**Examples:**

```bash
# Simple word matching (partial)
./bin/benchmark "Y2F0" "tests/simple_test.txt" "0"

# Email pattern matching (partial)
./bin/benchmark "W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ==" "tests/test_data.txt" "0"

# Full string matching
./bin/benchmark "aGVsbG8gd29ybGQ=" "tests/full_match_test.txt" "1"
```

**Output format:** `{elapsed_time:.6f} - {match_count}`

## Directory Structure

```
srm/
├── Benchmark.cs              # Main program source
├── benchmark.csproj          # .NET project file
├── Makefile                  # Build configuration
├── README.md                 # Documentation
└── tests/                    # Test suite
    ├── run_tests.sh          # Comprehensive test runner
    ├── simple_test.sh        # Simple test script
    ├── test_data.txt         # Comprehensive test data
    ├── simple_test.txt       # Simple test data
    └── full_match_test.txt   # Full match test data
``` 