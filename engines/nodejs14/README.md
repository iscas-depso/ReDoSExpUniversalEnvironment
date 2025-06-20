# Benchmark Program - Node.js 14

## Files
- `benchmark.js` - Main benchmark program using traditional Node.js 14 features
- `package.json` - Node.js package configuration with CommonJS module system
- `Makefile` - Build configuration with nvm-managed Node.js 14 environment
- `bin/benchmark` - Executable wrapper script enforcing Node.js 14 environment (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## Node.js 14 Features Used

This implementation uses traditional Node.js 14 features for maximum compatibility:

- **CommonJS Modules**: Uses `require()` and `module.exports` for module loading
- **Traditional Functions**: Standard function declarations and expressions
- **Performance Hooks**: Uses `performance.now()` for high-precision timing
- **Buffer API**: Traditional `Buffer.from()` for base64 decoding
- **Synchronous File I/O**: Uses `fs.readFileSync()` for consistent timing
- **Traditional Error Handling**: Standard try-catch blocks and error throwing
- **Callback Patterns**: Compatible with traditional Node.js async patterns

## Environment Management

This implementation uses **nvm (Node Version Manager)** for environment isolation:

- **Dedicated Node.js Version**: Enforces Node.js 14.21.3
- **nvm Integration**: Automatically switches to correct Node.js version
- **Environment Isolation**: Completely separate from Node.js 21 implementation
- **Fallback Support**: Falls back to system Node.js if nvm unavailable

## Building and Running

### Setup Node.js 14 environment
```bash
# Install nvm (if not already installed)
make install-nvm

# Setup Node.js 14
make setup-node

# Install dependencies
make install-deps
```

### Build the program
```bash
# Build the Node.js 14 benchmark program
make all

# Check Node.js 14 version
make node-version

# Alternative: run directly with Node.js
node benchmark.js <base64_regex> <filename> <match_mode>
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

Node.js 14 provides stable and reliable performance:

- **Mature V8 Engine**: Well-optimized JavaScript execution
- **Traditional JIT Compilation**: Proven optimization patterns
- **Stable Memory Management**: Predictable garbage collection
- **Excellent Compatibility**: Works across various environments

## Requirements

- **Node.js**: 14.0.0 or higher (specifically targets 14.21.3)
- **nvm**: Node Version Manager for environment isolation (recommended)
- **Make**: For build automation (optional)

## Directory Structure

```
nodejs14/
├── benchmark.js          # Main benchmark program (Node.js 14 features)
├── package.json          # Package configuration (CommonJS)
├── Makefile             # Build configuration (nvm-managed)
├── README.md            # This documentation
├── bin/                 # Executables (created during build)
│   └── benchmark        # Executable wrapper script (Node.js 14 enforced)
└── tests/               # Test suite
    ├── run_tests.sh     # Comprehensive test runner
    ├── simple_test.sh   # Simple test script
    ├── test_data.txt    # Comprehensive test data
    ├── simple_test.txt  # Simple test data
    └── full_match_test.txt # Full match test data
```

## Comparison with Node.js 21 Implementation

| Feature | Node.js 14 | Node.js 21 |
|---------|------------|-------------|
| Module System | CommonJS | ES Modules |
| Import Style | `require()` | `import` |
| Variables | `const`/`let` | Destructuring |
| String Matching | `.match()` | `.matchAll()` |
| Error Handling | Standard | Custom Classes |
| Optional Chaining | Not available | `?.` operator |
| Performance | Stable | Enhanced |

This implementation demonstrates traditional Node.js development patterns while maintaining complete compatibility with the project's interface standards. 