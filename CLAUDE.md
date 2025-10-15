# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **refactored ReDoS (Regular Expression Denial of Service) testing environment**. The goal is to optimize the Docker build process by pre-building tools and engines locally, then copying binaries into the container instead of compiling everything during Docker image build.

**Original Problem**: The old project (`/root/Refactoring/old/ReDoSExpUniversalEnvironment`) compiled all tools and engines during Docker build, requiring massive memory (130GB for regulator's V8 compilation) and long build times, making it impossible to build on most machines.

**Refactoring Goal**: Pre-build tools and engines locally, copy only binaries/executables into Docker, dramatically reducing build time and memory requirements.

## Project Structure

```
new/ReDoSExpUniversalEnvironment/
├── tools/              # ReDoS detection tools (6 tools)
│   ├── rescue/         # Static analyzer
│   ├── regexstatic/    # Static analyzer
│   ├── regexploit/     # Python-based detector
│   ├── rengar/         # Java-based detector
│   ├── regulator/      # V8-based detector (memory intensive)
│   └── redoshunter/    # GraalVM native image detector
├── engines/            # Regex engines for testing (19 engines)
│   ├── c/             # PCRE2-based C engine
│   ├── python/        # Python re module
│   ├── nodejs21/      # Node.js with V8 engine
│   └── ...            # (16 more engines)
├── Gen.py             # Main attack generation script
├── Verify.py          # Attack verification script
└── Dockerfile         # Container definition
```

## Core Workflow

### 1. Attack Generation (`Gen.py`)
- **Input**: Text file with regexes (one per line)
- **Output**: SQLite database with attack results
- Runs all 6 tools against each regex to detect ReDoS vulnerabilities
- Uses hyperfine for benchmarking
- Multi-threaded execution (80% of CPU cores)
- System resource monitoring (pauses if CPU/memory > 90%)

### 2. Attack Verification (`Verify.py`)
- **Input**: Database from Gen.py, max file size (KB), match mode (0=partial, 1=full)
- **Output**: Verification results added to database
- Tests generated attack strings against all 19 engines
- Measures actual execution time to confirm ReDoS
- Uses hyperfine for accurate timing

### 3. Tool Contract
Every tool must have a `run.py` following this contract:
- **Args**: `<base64_regex> <output_json_path>`
- **Output**: JSON file with:
  ```json
  {
    "elapsed_ms": <number>,
    "is_redos": <boolean>,
    "prefix": "<base64_string>",
    "infix": "<base64_string>",
    "suffix": "<base64_string>",
    "repeat_times": <number or -1>
  }
  ```

### 4. Engine Contract
Every engine must have a binary at `bin/benchmark` following this contract:
- **Args**: `<base64_regex> <text_file_path> <match_mode>`
  - `match_mode`: 0 = partial match, 1 = full match
- **Output**: `{elapsed_ms} - {match_count}`
  - `elapsed_ms`: 6 decimal places
  - `match_count`: number of matches found

## Commands

### Docker Operations
```bash
# Build Docker image (from new/ReDoSExpUniversalEnvironment/)
docker build --rm -t redos-test .

# Run attack generation
docker run --rm -v $(pwd):/workspace redos-test python3 Gen.py /workspace/regexes.txt /workspace/results.db

# Run verification
docker run --rm -v $(pwd):/workspace redos-test python3 Verify.py /workspace/results.db 100 0
```

### Tool Development
```bash
# Build a tool
cd tools/<tool_name>
make all

# Test a tool
make test

# Run tool manually (following contract)
python3 run.py <base64_regex> output.json
```

### Engine Development
```bash
# Build an engine
cd engines/<engine_name>
make all

# Test an engine
make test

# Run engine manually
./bin/benchmark <base64_regex> <text_file> <0|1>
```

### Git Workflow
```bash
# Initialize repository (if not already done)
cd /root/Refactoring/new/ReDoSExpUniversalEnvironment
git init

# After completing refactoring of a tool/engine and testing it works in Docker
git add .
git commit -m "Refactor <tool/engine name>: pre-build locally and copy to Docker

- Move compilation from Dockerfile to local build
- Update Dockerfile to copy pre-built binaries
- Test successful execution in container"
```

## Refactoring Strategy

### ⚠️ CRITICAL RULE: Docker Image Rebuilding

**WHENEVER the Dockerfile is modified, you MUST immediately rebuild the Docker image.**

This is **NON-NEGOTIABLE** and applies to:
- Adding new `COPY` instructions for tools/engines
- Installing new runtime dependencies (apt-get packages)
- Modifying any RUN commands
- Changing base image or environment variables

**Rebuild command:**
```bash
cd /root/Refactoring/new/ReDoSExpUniversalEnvironment
docker build --rm -t redos-test .
```

**Testing workflow:**
1. Modify Dockerfile (add COPY, install dependencies, etc.)
2. **IMMEDIATELY rebuild Docker image** ← DO NOT SKIP THIS
3. Test components in the NEW Docker container
4. If tests pass, commit changes
5. If tests fail, fix issues and repeat from step 1

**Why this matters:**
- Old Docker images don't have new dependencies or files
- Testing with old images gives false negatives
- Wastes time debugging non-existent problems

### For Each Tool:
1. **ALWAYS reference the old project configuration first** - check `/root/Refactoring/old/ReDoSExpUniversalEnvironment/` for Dockerfile setup, runtime testing, and tool implementation
2. Analyze current Dockerfile build steps in old project
3. Create local build process (Makefile if needed)
4. Build tool locally to generate binaries/artifacts
5. Modify Dockerfile to `COPY` pre-built artifacts instead of building
6. **REBUILD Docker image immediately** ← CRITICAL
7. Test tool execution inside Docker container
8. Git commit when successful

### For Each Engine:
1. **ALWAYS reference the old project configuration first** - check `/root/Refactoring/old/ReDoSExpUniversalEnvironment/` for Dockerfile environment setup, testing approach, and engine implementation
2. Analyze dependencies and compilation requirements from old project
3. Build engine locally (using existing Makefile)
4. Identify which binaries/files are needed at runtime
5. Modify Dockerfile to `COPY` only runtime artifacts
6. **REBUILD Docker image immediately** ← CRITICAL
7. Test engine inside Docker with test suite
8. Git commit when successful

### Special Cases:
- **Node.js engines** (nodejs14, nodejs21): May need to copy node_modules or use global installs
- **Regulator**: Most challenging - requires V8 compilation, focus on this last
- **GraalVM tools** (redoshunter): Native image compilation can be done locally
- **Rust/Go**: Static binaries work well, just copy the executable

## Testing Approach

For initial refactoring stages:
- **Focus on tools and engines only**
- Skip batch processing and comprehensive testing scripts
- Test each tool/engine individually after refactoring
- Use simple test cases to verify functionality
- Ensure Docker execution works before committing

## Key Considerations

- **Memory constraints**: Pre-building avoids the 130GB memory requirement for regulator
- **Network issues**: Local builds avoid network failures during Docker build
- **Build time**: Goal is dramatically faster Docker image creation
- **Binary compatibility**: Ensure locally-built binaries are compatible with Ubuntu 22.04 base image
- **Dependencies**: Runtime dependencies must still be installed in Dockerfile (shared libraries, etc.)

## Working Directory

Always work in: `/root/Refactoring/new/ReDoSExpUniversalEnvironment/`

The old project is available for reference at: `/root/Refactoring/old/ReDoSExpUniversalEnvironment/`
