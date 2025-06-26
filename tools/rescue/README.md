# ReDoS regex attack string generate tools

## Files
- `run.py` - Main entry point following project contract
- `src/` - Source code directory containing Java source files
- `pom.xml` - Maven build configuration
- `tests/` - Test scripts and test data
- `tests/simple_test.sh` - Basic functionality tests
- `original_test/` - Original ReScue test framework and data
- `Makefile` - Build and test automation

## Building and Running
### Build
```bash
make all
```
This will compile the Java code and create the JAR file using Maven.

### Run tests
```bash
make test
```

## Program Usage
The tool follows the standard project contract:

**Arguments:**
1. Base64 encoded regex pattern
2. Output file path

**Output:**
JSON file with the following format:
```json
{
  "elapsed_ms": "elapsed_ms",
  "is_redos": true or false,
  "prefix": "a base64 encoded prefix of attack string (empty for ReScue)",
  "infix": "a base64 encoded infix of attack string (the full attack string)",
  "suffix": "a base64 encoded suffix of attack string (empty for ReScue)",
  "repeat_times": 1
}
```

**Example:**
```bash
# Test with known ReDoS pattern (a+)+
python3 run.py "KGErKSs=" output.json
```

## Technology
ReScue uses genetic algorithms to find ReDoS attack strings by:
- Converting regexes into extended NFA (eNFA) representation
- Using genetic algorithms to evolve candidate attack strings
- Employing crossover, mutation, and selection operators
- Testing candidate strings against the regex to measure execution time
- Finding strings that cause exponential backtracking behavior

The genetic algorithm approach allows ReScue to discover complex attack patterns that may not be obvious through static analysis.

## Directory Structure
```
rescue/
├── run.py                   # Main entry point
├── README.md               # This file
├── Makefile               # Build automation
├── pom.xml                # Maven configuration
├── src/                   # Java source code
│   └── cn/edu/nju/moon/redos/
