# ReDoS regex attack string generate tools - GREWIA

## Files
- `GREWIA.cpp` - Main GREWIA tool source code (modified to accept base64 regex and output JSON)
- `run.py` - Python wrapper script following project contract
- `Solver/` - Core solver implementation 
- `Parser/` - Regex parser implementation
- `Membership/` - Membership testing components
- `CMakeLists.txt` - Build configuration
- `build/` - Build directory (created during build)

## Building and Running

### Dependencies
- gcc 11.4.0 or compatible
- cmake version 3.22.1 or higher
- libssl-dev (for base64 encoding/decoding)
- nlohmann-json3-dev (for JSON output)

### Setup
```bash
sudo apt install build-essential cmake libssl-dev nlohmann-json3-dev
```

### Build
```bash
cd tools/GREWIA
mkdir -p build && cd build
cmake ..
make -j
```

### Run tests
```bash
# Test with the Python wrapper (recommended)
python3 run.py <base64_regex> <output_json_file>

# Direct executable usage
./build/GREWIA <base64_regex> <output_json_file> <output_directory> <attack_string_length> <simplified_mode_on> <decremental_on> <matching_function> <regex_engine>
```

## Program Usage

### Using run.py (Recommended)
```bash
# Example with base64 encoded regex "(a+)+"
python3 run.py KGErKSs= output.json
```

### Direct executable usage
```bash
# Parameters:
# 1. Base64 encoded regex
# 2. Output JSON file path  
# 3. Output directory for temporary files
# 4. Attack string length (e.g., 100000)
# 5. Simplified mode (1=single attack string, 0=series)
# 6. Decremental method (1=on, 0=off)
# 7. Matching function (1=partial match, 0=full match)
# 8. Regex engine (Java, JavaScript, Perl, PHP, Python, Boost, C#)

./build/GREWIA KGErKSs= output.json /tmp/grewia_output 100000 1 0 1 Java
```

### Output Format
The tool outputs a JSON file with the following format:
```json
{
  "elapsed_ms": "execution_time_in_milliseconds",
  "is_redos": true,
  "prefix": "base64_encoded_prefix_of_attack_string",
  "infix": "base64_encoded_infix_of_attack_string", 
  "suffix": "base64_encoded_suffix_of_attack_string",
  "repeat_times": -1
}
```

## Directory Structure
```
tools/GREWIA/
├── GREWIA.cpp          # Main source file
├── run.py              # Python wrapper script
├── Readme.md           # This file
├── CMakeLists.txt      # Build configuration
├── build/              # Build directory (created by build)
│   └── GREWIA          # Compiled executable
├── Solver/             # Solver implementation
│   ├── solver.cpp
│   ├── String/
│   └── ...
├── Parser/             # Parser implementation
│   ├── parser.cpp
│   └── ...
└── Membership/         # Membership testing
    └── ...
```

