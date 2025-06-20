# Multi-Language Regex Benchmark Test Suite

This repository contains regex benchmark implementations in 19 different programming languages and frameworks, organized under the `engines/` directory.

## Quick Start

### 1. Build the Docker Image
```bash
docker build --rm -t benchmark-test .
```

### 2. Run All Tests

#### Windows (Batch Script)
```cmd
# Test all engines
test_all_engines.bat

# Test a single engine
test_single_engine.bat c
test_single_engine.bat python
test_single_engine.bat nodejs21
```

#### Unix/Linux/macOS (Bash Script)
```bash
# Test all engines
./run_all_tests.sh

# Test specific engines
./test_engine.sh c
./test_engine.sh python nodejs21 rust
```

#### PowerShell (Cross-platform)
```powershell
# Test all engines
PowerShell -ExecutionPolicy Bypass -File .\run_all_tests.ps1
```

## Available Engines

The following regex engines are available for testing:

| Engine | Language/Framework | Notes |
|--------|-------------------|-------|
| `awk` | GNU AWK | |
| `c` | C with PCRE2 | |
| `cpp` | C++ with Boost.Regex | |
| `csharp` | C# .NET 7.0 | |
| `csharp_nonbacktracking` | C# Non-Backtracking | |
| `go` | Go | |
| `grep` | GNU grep | |
| `hyperscan` | Intel Hyperscan | |
| `java8` | Java 8 | |
| `java11` | Java 11 | |
| `nodejs14` | Node.js 14.21.3 | |
| `nodejs21` | Node.js 21.7.3 | With V8 non-backtracking engine |
| `perl` | Perl | |
| `php` | PHP | |
| `python` | Python 3 | |
| `re2` | Google RE2 | |
| `ruby` | Ruby | |
| `rust` | Rust | |
| `srm` | SRM (Statistical Regex Matcher) | |

## Script Features

### Comprehensive Testing
- ✅ Tests all 19 engines automatically
- ✅ Runs each engine's complete test suite
- ✅ Shows pass/fail status for each engine
- ✅ Provides detailed test output
- ✅ Colorized output for easy reading
- ✅ Summary statistics at the end

### Cross-Platform Support
- **Windows**: Use `.bat` files for simplicity
- **Unix/Linux/macOS**: Use `.sh` bash scripts
- **PowerShell**: Cross-platform PowerShell script

### Flexible Usage
- Run all engines at once
- Run specific engines only
- Individual engine testing
- Detailed error reporting

## Test Output Format

Each engine's benchmark program outputs results in the format:
```
{elapsed_time_ms} - {match_count}
```

Example:
```
0.069923 - 5
```
This means the regex took 0.069923 milliseconds and found 5 matches.

## Test Cases

Each engine runs the same standardized test cases:
1. **Simple word match** (partial): "cat" pattern
2. **Email pattern match** (partial): Complex email regex
3. **Digit pattern match** (partial): `\d+` pattern  
4. **Full match test**: "hello world" exact match
5. **Full match fail test**: "hello" should not match "hello world"
6. **Word boundary test**: `\bcat\b` pattern

## Project Structure

```
ReDoSExpUniversalEnvironment/
├── engines/                    # All benchmark engines
│   ├── awk/                   # AWK implementation
│   ├── c/                     # C implementation
│   ├── cpp/                   # C++ implementation
│   ├── csharp/                # C# implementation
│   ├── ...                    # (19 engines total)
│   └── srm/                   # SRM implementation
├── Dockerfile                 # Docker container definition
├── test_all_engines.bat      # Windows: Test all engines
├── test_single_engine.bat    # Windows: Test single engine
├── run_all_tests.sh          # Unix: Test all engines
├── test_engine.sh            # Unix: Test specific engines
├── run_all_tests.ps1         # PowerShell: Test all engines
└── README.md                 # This file
```

## Individual Engine Testing

You can also test engines individually by running commands directly:

```bash
# Test C implementation
docker run --rm benchmark-test bash -c "cd /app/engines/c && make test"

# Test Python implementation  
docker run --rm benchmark-test bash -c "cd /app/engines/python && make test"

# Test Node.js 21 (special case)
docker run --rm benchmark-test bash -c "source /home/developer/.nvm/nvm.sh && nvm use 21.7.3 && cd /app/engines/nodejs21 && make test"
```

## Troubleshooting

### Docker Image Not Found
If you see "Docker image 'benchmark-test' not found":
```bash
docker build --rm -t benchmark-test .
```

### Script Execution Issues
For PowerShell scripts on Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

For bash scripts on Unix systems:
```bash
chmod +x *.sh
```

### Individual Engine Failures
If a specific engine fails, you can test it individually to see detailed error messages:
```bash
# Windows
test_single_engine.bat <engine_name>

# Unix/Linux/macOS  
./test_engine.sh <engine_name>
``` 