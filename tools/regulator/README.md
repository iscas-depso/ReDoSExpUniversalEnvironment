# ReDoS regex attack string generate tools

## Files
- `run.py` - Main entry point script that follows the project contract
- `Makefile` - Build script for the tool
- `regulator-dynamic/` - Source code from https://github.com/ucsb-seclab/regulator-dynamic.git
- `tests/` - Test files and data
- `README.md` - This file

## Building and Running
### Build
```bash
make all
```
This will:
1. Build the regulator-dynamic fuzzer from source
2. Install Python dependencies for the driver
3. Set up the run.py script

### Run tests
```bash
make test
```

## Program Usage
The tool follows the project contract:

**Input:**
1. Base64 encoded regex pattern
2. Output file path

**Output:**
JSON file with format:
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
# Create base64 encoded regex
echo -n "(a+)+b" | base64
# Output: KGErKSti

# Run the tool
python3 run.py "KGErKSti" output.json

# Check results
cat output.json
```

## Directory Structure
```
tools/regulator/
├── run.py              # Main entry point
├── Makefile           # Build script
├── README.md          # This file
├── regulator-dynamic/ # Source code from upstream
│   ├── fuzzer/        # C++ fuzzer source
│   ├── driver/        # Python driver source
│   └── ...
└── tests/             # Test files
```

## About Regulator
Regulator is a fuzzer/dynamic analysis tool to detect ReDoS in JavaScript regular expressions. It's published in USENIX Security '22. This implementation adapts the original tool to work within the project's unified interface.

The tool performs fuzzing to find potential ReDoS vulnerabilities, then uses pumping analysis to classify the vulnerability and extract attack string components. 