# Benchmark Program - Node.js 21

## Files
- `benchmark.js` - Main benchmark program using modern Node.js 21 features
- `package.json` - Node.js package configuration with ES Modules enabled
- `Makefile` - Build configuration with nvm-managed Node.js 21 environment
- `bin/benchmark` - Executable wrapper script enforcing Node.js 21 environment (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## Node.js 21 Features Used

This implementation showcases modern Node.js 21 features for enhanced performance and developer experience:

- **Array Destructuring**: Modern assignment patterns like `const [, , arg1, arg2] = process.argv`
- **Custom Error Classes**: Enhanced error handling with custom error types  
- **Enhanced Validation**: Modern validation patterns and error handling
- **Advanced Error Handling**: Global exception and rejection handlers
- **Modern Buffer Handling**: Enhanced base64 decoding with validation
- **Template Literals**: Modern string formatting and interpolation
- **Arrow Functions**: Concise function syntax where appropriate
- **Enhanced Performance API**: High-precision timing with `performance.now()`

## Environment Management

This implementation uses **nvm (Node Version Manager)** for environment isolation:

- **Dedicated Node.js Version**: Enforces Node.js 21.7.3
- **nvm Integration**: Automatically switches to correct Node.js version
- **Environment Isolation**: Completely separate from Node.js 14 implementation
- **Modern Runtime**: Takes advantage of latest V8 optimizations

## Building and Running

### Setup Node.js 21 environment
```bash
# Install nvm (if not already installed)
make install-nvm

# Setup Node.js 21
make setup-node

# Install dependencies
make install-deps
```

### Build the program
```bash
# Build the Node.js 21 benchmark program
make all

# Check Node.js 21 version
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
# Output example: 0.987654 - 5

# Search for email patterns in test_data.txt
./bin/benchmark W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== tests/test_data.txt 0
```

2. **Full matching** (entire text must match):
```bash
# Check if entire file matches "hello world"
./bin/benchmark aGVsbG8gd29ybGQ= tests/full_match_test.txt 1
# Output example: 0.654321 - 1

# Check if entire file matches "hello" (should fail)
./bin/benchmark aGVsbG8= tests/full_match_test.txt 1
# Output example: 0.543210 - 0
```

## Performance Characteristics

Node.js 21 provides cutting-edge performance improvements:

- **Enhanced V8 Engine**: Latest JavaScript optimizations and features
- **Improved JIT Compilation**: Better optimization patterns and memory usage
- **Modern Garbage Collection**: More efficient memory management
- **Native ES Modules**: Faster module loading and resolution
- **Advanced Regex Engine**: Optimized string matching operations

## Requirements

- **Node.js**: 21.0.0 or higher (specifically targets 21.7.3)
- **nvm**: Node Version Manager for environment isolation (recommended)
- **Make**: For build automation (optional)

## Directory Structure

```
nodejs21/
├── benchmark.js          # Main benchmark program (Node.js 21 features)
├── package.json          # Package configuration (ES Modules)
├── Makefile             # Build configuration (nvm-managed)
├── README.md            # This documentation
├── bin/                 # Executables (created during build)
│   └── benchmark        # Executable wrapper script (Node.js 21 enforced)
└── tests/               # Test suite
    ├── run_tests.sh     # Comprehensive test runner
    ├── simple_test.sh   # Simple test script
    ├── test_data.txt    # Comprehensive test data
    ├── simple_test.txt  # Simple test data
    └── full_match_test.txt # Full match test data
```

## Modern JavaScript Features Showcase

### ES Modules
```javascript
import fs from 'fs/promises';
import { readFileSync } from 'fs';
```

### Array Destructuring
```javascript
const [, , base64Regex, filename, matchModeStr] = process.argv;
```

### Optional Chaining
```javascript
if (!base64String?.length) {
    throw new BenchmarkError('Base64 string cannot be empty');
}
```

### String.matchAll()
```javascript
const matches = [...data.matchAll(new RegExp(patternStr, 'g'))];
```

### Custom Error Classes
```javascript
class BenchmarkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'BenchmarkError';
    }
}
```

## Comparison with Node.js 14 Implementation

| Feature | Node.js 14 | Node.js 21 |
|---------|------------|-------------|
| Module System | CommonJS | ES Modules |
| Import Style | `require()` | `import` |
| Variables | Standard | Destructuring |
| String Matching | `.match()` | `.matchAll()` |
| Error Handling | Standard | Custom Classes |
| Optional Chaining | Not available | `?.` operator |
| Performance | Stable | Enhanced |
| Memory Usage | Higher | Optimized |

This implementation demonstrates the evolution of JavaScript and Node.js while maintaining complete compatibility with the project's interface standards. 