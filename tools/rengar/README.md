# ReDoS regex attack string generate tools

## Files
- `run.py` - Entry point script that follows the project contract
- `Rengar.jar` - Pre-compiled Java executable (will be built from source)
- `src/` - Java source code directory
- `Makefile` - Build script for compiling from source
- `tests/` - Test files and scripts

## Building and Running
### Build
```bash
make build
```

This will:
1. Clean any previous build artifacts
2. Compile the Java source code using Maven
3. Create the JAR file with dependencies
4. Copy the JAR to the root directory as `Rengar.jar`

Requirements:
- Java 17 or later
- Maven 3.6 or later

### Run tests
```bash
make test
```

## Program Usage
The tool follows the project contract:

```bash
python run.py <base64_regex> <output_file_path>
```

Example:
```bash
python run.py "KGEqKXsyLH0=" output.json
```

### Input
- `base64_regex`: Base64 encoded regular expression
- `output_file_path`: Path to output JSON file

### Output
JSON file with the following format:
```json
{
  "elapsed_ms": "elapsed_ms",
  "is_redos": true,
  "prefix": "base64_encoded_prefix",
  "infix": "base64_encoded_infix", 
  "suffix": "base64_encoded_suffix",
  "repeat_times": "recommended_repeat_times"
}
```

If the regex is not vulnerable to ReDoS:
```json
{
  "elapsed_ms": "elapsed_ms",
  "is_redos": false
}
```

## Directory Structure
```
tools/rengar/
├── run.py                          # Entry point script
├── Rengar.jar                      # Compiled JAR file
├── Makefile                        # Build script
├── README.md                       # This file
├── src/                           # Java source code
│   ├── main/
│   │   └── java/
│   │       └── rengar/
│   │           ├── checker/
│   │           │   └── attack/
│   │           │       └── AttackString.java
│   │           └── cli/
│   │               └── Main.java
│   ├── pom.xml                    # Maven configuration
│   └── target/                    # Build output (created during build)
└── tests/                         # Test files (to be created)
``` 