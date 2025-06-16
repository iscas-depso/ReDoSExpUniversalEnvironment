# Benchmark Program - Node.js 21 with V8 Non-Backtracking RegExp Engine

## Files
- `benchmark.js` - Main benchmark program using V8's experimental non-backtracking RegExp engine
- `package.json` - Node.js package configuration with non-backtracking engine support
- `Makefile` - Build configuration with V8 experimental flags enabled
- `bin/benchmark` - Executable wrapper script with non-backtracking engine flags (created after building)
- `tests/run_tests.sh` - Comprehensive test runner covering all functionality
- `tests/simple_test.sh` - Quick test script for basic validation
- `tests/test_data.txt` - Comprehensive test dataset with various text patterns
- `tests/simple_test.txt` - Simple test dataset for basic testing
- `tests/full_match_test.txt` - Test data specifically for full match testing

## V8 Non-Backtracking RegExp Engine Features

This implementation uses V8's experimental non-backtracking RegExp engine for enhanced security and performance:

- **Linear-Time Execution**: Prevents catastrophic backtracking (ReDoS attacks)
- **Automatic Fallback**: Falls back to standard engine when backtracking exceeds threshold
- **Linear Engine Flag**: Uses `/l` flag for guaranteed linear-time execution
- **Engine Detection**: Automatically detects and adapts to engine availability
- **Security Enhancement**: Immune to ReDoS attacks caused by malicious patterns
- **Performance Optimization**: Better performance on complex patterns
- **Modern Error Handling**: Graceful fallback when linear engine constructs are unsupported
- **V8 Version Detection**: Runtime detection of V8 engine capabilities

## Modern Node.js 21 Features Used

Additionally includes modern Node.js 21 features:

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
# Build the Node.js 21 benchmark program with V8 non-backtracking engine
make all

# Check Node.js 21 version
make node-version

# Alternative: run directly with Node.js (requires experimental flags)
node --enable-experimental-regexp-engine benchmark.js <base64_regex> <filename> <match_mode>

# Run with auto-fallback mode
node --enable-experimental-regexp_engine-on-excessive-backtracks benchmark.js <base64_regex> <filename> <match_mode>

# Run with both flags (recommended)
node --enable-experimental-regexp-engine --enable-experimental-regexp_engine-on-excessive-backtracks benchmark.js <base64_regex> <filename> <match_mode>
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

Node.js 21 with V8 Non-Backtracking RegExp Engine provides:

### Security Benefits
- **ReDoS Prevention**: Immune to Regular Expression Denial of Service attacks
- **Linear Time Complexity**: O(n×m) instead of potentially exponential complexity
- **Predictable Performance**: No catastrophic slowdowns on malicious inputs
- **Memory Safety**: Bounded memory usage during pattern matching

### Performance Benefits
- **Enhanced V8 Engine**: Latest JavaScript optimizations with experimental RegExp engine
- **Improved Pattern Matching**: Linear-time execution for complex patterns
- **Auto-Fallback**: Best of both worlds - security when needed, speed when possible
- **Modern Garbage Collection**: More efficient memory management
- **Advanced Regex Engine**: Dual-engine approach for optimal performance

### V8 Engine Modes
- **Force Linear**: `--enable-experimental-regexp-engine` - Always use linear engine
- **Auto-Fallback**: `--enable-experimental-regexp_engine-on-excessive-backtracks` - Switch when needed
- **Hybrid Mode**: Both flags for maximum security and performance

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

## V8 Non-Backtracking Engine Usage Examples

### Basic Usage with Linear Engine
```bash
# Enable linear engine for all patterns
node --enable-experimental-regexp-engine benchmark.js <base64_regex> <filename> <mode>
```

### Auto-Fallback Mode (Recommended)
```bash
# Auto-switch to linear engine when backtracking threshold is exceeded
node --enable-experimental-regexp_engine-on-excessive-backtracks benchmark.js <base64_regex> <filename> <mode>
```

### Hybrid Mode (Maximum Security)
```bash
# Use both flags for best security and performance
node --enable-experimental-regexp-engine --enable-experimental-regexp_engine-on-excessive-backtracks benchmark.js <base64_regex> <filename> <mode>
```

### Engine Detection
The program automatically detects linear engine support:
```javascript
// Internal engine detection
function detectV8LinearEngineSupport() {
    try {
        new RegExp('test', 'l');  // Try /l flag
        return true;
    } catch (e) {
        return false;
    }
}
```

### Pattern Compatibility
- **Supported**: Basic patterns, character classes, quantifiers, alternation
- **Unsupported**: Backreferences, lookahead/lookbehind, some complex constructs
- **Fallback**: Automatic fallback to standard engine for unsupported constructs

### Debugging V8 Engine
```bash
# Enable debug output
NODE_DEBUG=benchmark node --enable-experimental-regexp-engine benchmark.js <args>
```

## ReDoS Protection Examples

The non-backtracking engine protects against catastrophic backtracking:

```javascript
// These patterns could cause ReDoS with standard engine:
// (a*)*b     - nested quantifiers
// (a+)+      - possessive quantifiers
// (a|a)*     - alternation with overlap

// With linear engine (/l flag), they execute in linear time
const pattern = new RegExp('(a*)*b', 'l');  // Safe with linear engine
```

## Version Requirements

- **Node.js**: 21.0.0+ (includes V8 with experimental engine)
- **V8 Version**: 8.8+ (required for non-backtracking engine)
- **Runtime Flags**: Required for engine activation 