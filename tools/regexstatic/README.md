# ReDoS regex attack string generate tools

## Files
- `run.py` - Main entry point following project contract
- `src/` - Source code directory containing Java source files
- `pom.xml` - Maven build configuration
- `tests/` - Test scripts and test data
- `tests/simple_test.sh` - Basic functionality tests
- `test_data/` - Test data files for regex patterns
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
  "prefix": "a base64 encoded prefix of attack string",
  "infix": "a base64 encoded infix of attack string", 
  "suffix": "a base64 encoded suffix of attack string",
  "repeat_times": "the repeat times of the infix in the attack string which recommended by the tool"
}
```

**Example:**
```bash
# Test with known exponential ReDoS pattern (a+)+
python3 run.py "KGErKSs=" output.json
```

## Technology
RegexStatic performs static analysis on regular expressions to determine ReDoS vulnerabilities by:
- Analyzing the underlying NFA (Non-deterministic Finite Automaton) structure
- Detecting EDA (Exponential Degree of Ambiguity) for exponential ReDoS
- Detecting IDA (Infinite Degree of Ambiguity) for polynomial ReDoS  
- Constructing exploit strings when vulnerabilities are found

## Directory Structure
```
regexstatic/
├── run.py                   # Main entry point
├── README.md               # This file
├── Makefile               # Build automation
├── pom.xml                # Maven configuration
├── src/                   # Java source code
│   └── main/
