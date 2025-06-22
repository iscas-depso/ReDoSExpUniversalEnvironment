# ReDoS regex attack string generate tools - ReDoSHunter

## Files
- `src/` - ReDoSHunter Java source code and dependencies
- `run.py` - Python wrapper script for tool execution
- `Makefile` - Build script for compiling the tool
- `tests/` - Test files and scripts
- `README.md` - This documentation

## Building and Running
### Build
```bash
make all
```

### Run tests
```bash
make test
```

## Program Usage
```bash
python3 run.py <base64_regex> <output_file_path>
```

Example:
```bash
python3 run.py YStbXCt8KGEqKSspJA== /tmp/output.json
```

## Directory Structure
```
redoshunter/
├── src/
│   ├── src/main/java/...    # Java source files
│   ├── pom.xml              # Maven configuration
│   └── ...                  # Other source files
├── run.py                   # Python wrapper
├── Makefile                 # Build configuration
├── tests/
│   └── simple_test.sh       # Basic test script
└── README.md                # This file
```

## About ReDoSHunter
ReDoSHunter is a combined static and dynamic approach for regular expression DoS detection. This tool analyzes regular expressions to detect potential ReDoS vulnerabilities and generates attack strings when vulnerabilities are found.

The tool supports multiple vulnerability pattern types:
- NQ (Nested Quantifiers)
- EOD (Exponential on Demand)
- EOA (Exponential on Alternation)  
- POA (Polynomial on Alternation)
- SLQ (Star Height and Length Quantifiers) 