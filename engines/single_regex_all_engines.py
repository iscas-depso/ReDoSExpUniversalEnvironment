#!/usr/bin/env python3
"""
Single Regex All Engines Test Script

This script runs a single regex test across all available engines in the benchmark suite.
It takes the same arguments as individual benchmark programs and tests them on every engine.

Usage: python3 single_regex_all_engines.py <base64_regex> <text_file> <mode>
  - base64_regex: Regular expression encoded in Base64
  - text_file: Path to the text file to search in
  - mode: 0 for partial match, 1 for full match

Output: Results from all engines showing timing and match count
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# ANSI color codes for output formatting
class Colors:
    @staticmethod
    def _has_color_support():
        """Check if terminal supports colors"""
        import platform
        if platform.system() == "Windows":
            import os
            # Enable ANSI support on Windows 10+
            try:
                os.system("color")
            except:
                pass
            return True
        return True
    
    _color_enabled = _has_color_support()
    
    RED = '\033[0;31m' if _color_enabled else ''
    GREEN = '\033[0;32m' if _color_enabled else ''
    YELLOW = '\033[1;33m' if _color_enabled else ''
    BLUE = '\033[0;34m' if _color_enabled else ''
    CYAN = '\033[0;36m' if _color_enabled else ''
    MAGENTA = '\033[0;35m' if _color_enabled else ''
    BOLD = '\033[1m' if _color_enabled else ''
    NC = '\033[0m' if _color_enabled else ''

# List of all engines in the benchmark suite
ENGINES = [
    "awk",
    "c", 
    "cpp",
    "csharp",
    "csharp_nonbacktracking",
    "go",
    "grep", 
    "hyperscan",
    "java8",
    "java11",
    "nodejs14",
    "nodejs21",
    "perl",
    "php",
    "python",
    "re2", 
    "ruby",
    "rust",
    "srm"
]

def print_usage():
    """Print usage information."""
    print(f"{Colors.CYAN}Single Regex All Engines Test Script{Colors.NC}")
    print(f"{Colors.CYAN}===================================={Colors.NC}")
    print()
    print(f"{Colors.BOLD}Usage:{Colors.NC}")
    print(f"  python3 single_regex_all_engines.py <base64_regex> <text_file> <mode>")
    print()
    print(f"{Colors.BOLD}Arguments:{Colors.NC}")
    print(f"  base64_regex  : Regular expression encoded in Base64")
    print(f"  text_file     : Path to the text file to search in")
    print(f"  mode          : 0 for partial match, 1 for full match")
    print()
    print(f"{Colors.BOLD}Examples:{Colors.NC}")
    print(f"  # Test 'cat' pattern in simple test file (partial match)")
    print(f"  python3 single_regex_all_engines.py Y2F0 c/tests/simple_test.txt 0")
    print()
    print(f"  # Test email regex in test data (partial match)")
    print(f"  python3 single_regex_all_engines.py W2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfQ== c/tests/test_data.txt 0")

def check_engine_availability(engine_name):
    """Check if an engine is available and buildable."""
    engine_path = Path(engine_name)
    if not engine_path.exists():
        return False, f"Directory not found"
    
    makefile_path = engine_path / "Makefile"
    if not makefile_path.exists():
        return False, f"Makefile not found"
    
    return True, "Available"

def build_engine(engine_name):
    """Build an engine using its Makefile."""
    # Skip building for interpreted languages that might work without make
    interpreted_engines = ["python", "perl", "php", "ruby", "nodejs14", "nodejs21"]
    if engine_name in interpreted_engines:
        executable = get_engine_executable(engine_name)
        if executable:
            return True, "No build needed (interpreted language)"
    
    try:
        # Check if make is available
        import shutil
        if not shutil.which("make"):
            return False, "make command not found (run in Docker container)"
        
        result = subprocess.run(
            ["make", "all"],
            cwd=engine_name,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Build timeout"
    except Exception as e:
        return False, str(e)

def get_engine_executable(engine_name):
    """Get the executable path for an engine."""
    engine_path = Path(engine_name)
    
    # All engines should have bin/benchmark after make all
    bin_benchmark = engine_path / "bin" / "benchmark"
    if bin_benchmark.exists():
        return "bin/benchmark"
    
    # For AWK, it uses the source file directly
    if engine_name == "awk":
        awk_path = engine_path / "benchmark.awk"
        if awk_path.exists():
            return "benchmark.awk"
    
    return None

def run_engine_test(engine_name, base64_regex, text_file, mode):
    """Run a test on a specific engine."""
    executable = get_engine_executable(engine_name)
    if not executable:
        return False, "Executable not found", 0.0, 0
    
    # Convert text_file to absolute path to ensure it works from any engine directory
    engine_relative_file = os.path.abspath(text_file)
    
    # Prepare command based on engine type
    if engine_name == "awk":
        # AWK takes arguments directly, not as -v variables
        cmd = ["awk", "-f", executable, base64_regex, engine_relative_file, mode]
    else:
        # All other engines use bin/benchmark executable
        cmd = [f"./{executable}", base64_regex, engine_relative_file, mode]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=engine_name,
            capture_output=True,
            text=True,
            timeout=30
        )
        end_time = time.time()
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, error_msg, 0.0, 0
        
        # Parse output format: "elapsed_ms - match_count"
        output = result.stdout.strip()
        if ' - ' in output:
            parts = output.split(' - ')
            if len(parts) == 2:
                try:
                    elapsed_ms = float(parts[0])
                    match_count = int(parts[1])
                    return True, output, elapsed_ms, match_count
                except ValueError:
                    pass
        
        return False, f"Invalid output format: '{output}'", 0.0, 0
        
    except subprocess.TimeoutExpired:
        return False, "Execution timeout", 0.0, 0
    except Exception as e:
        return False, str(e), 0.0, 0

def main():
    """Main function."""
    if len(sys.argv) != 4:
        print_usage()
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    text_file = sys.argv[2]
    mode = sys.argv[3]
    
    # Validate mode
    if mode not in ["0", "1"]:
        print(f"{Colors.RED}Error: Mode must be 0 (partial) or 1 (full){Colors.NC}")
        sys.exit(1)
    
    # Check if text file exists (try relative to current dir and engine dirs)
    text_file_found = False
    if os.path.exists(text_file):
        text_file_found = True
    else:
        # Try to find the file in one of the engine test directories
        for engine in ENGINES[:3]:  # Check first few engines
            test_file_path = os.path.join(engine, "tests", os.path.basename(text_file))
            if os.path.exists(test_file_path):
                text_file = test_file_path
                text_file_found = True
                break
    
    if not text_file_found:
        print(f"{Colors.RED}Error: Text file '{text_file}' not found{Colors.NC}")
        sys.exit(1)
    
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    print(f"{Colors.CYAN}  Multi-Language Regex Benchmark - Single Test Mode{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}Note: This script is designed to run inside the Docker container{Colors.NC}")
    print(f"{Colors.YELLOW}      where all build tools and dependencies are available.{Colors.NC}")
    print()
    print(f"{Colors.BOLD}Test Parameters:{Colors.NC}")
    print(f"  Base64 Regex: {base64_regex}")
    print(f"  Text File:    {text_file}")
    print(f"  Mode:         {mode} ({'partial' if mode == '0' else 'full'} match)")
    print()
    
    results = []
    total_engines = len(ENGINES)
    successful_tests = 0
    
    for i, engine in enumerate(ENGINES, 1):
        print(f"{Colors.YELLOW}[{i:2d}/{total_engines}] Testing {engine}...{Colors.NC}", end=" ")
        
        # Check engine availability
        available, reason = check_engine_availability(engine)
        if not available:
            print(f"{Colors.RED}SKIP ({reason}){Colors.NC}")
            results.append((engine, "SKIP", reason, 0.0, 0))
            continue
        
        # Build engine if needed
        print(f"{Colors.BLUE}Building...{Colors.NC}", end=" ")
        built, build_error = build_engine(engine)
        if not built:
            print(f"{Colors.RED}BUILD FAILED{Colors.NC}")
            results.append((engine, "BUILD_FAILED", build_error[:50], 0.0, 0))
            continue
        
        # Run test
        print(f"{Colors.BLUE}Running...{Colors.NC}", end=" ")
        success, output, elapsed_ms, match_count = run_engine_test(engine, base64_regex, text_file, mode)
        
        if success:
            print(f"{Colors.GREEN}OK{Colors.NC}")
            results.append((engine, "SUCCESS", output, elapsed_ms, match_count))
            successful_tests += 1
        else:
            print(f"{Colors.RED}FAILED{Colors.NC}")
            results.append((engine, "FAILED", output[:50], 0.0, 0))
    
    # Print summary results
    print()
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    print(f"{Colors.CYAN}                        RESULTS SUMMARY{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    print()
    
    # Print header
    print(f"{Colors.BOLD}{'Engine':<20} {'Status':<12} {'Time (ms)':<12} {'Matches':<8} {'Details':<20}{Colors.NC}")
    print(f"{'-'*70}")
    
    # Sort results by elapsed time for successful tests
    successful_results = [(r[0], r[1], r[2], r[3], r[4]) for r in results if r[1] == "SUCCESS"]
    failed_results = [(r[0], r[1], r[2], r[3], r[4]) for r in results if r[1] != "SUCCESS"]
    successful_results.sort(key=lambda x: x[3])  # Sort by elapsed time
    
    # Print successful results
    for engine, status, output, elapsed_ms, match_count in successful_results:
        print(f"{Colors.GREEN}{engine:<20}{Colors.NC} "
              f"{Colors.GREEN}{status:<12}{Colors.NC} "
              f"{elapsed_ms:>10.6f}  "
              f"{match_count:>6}   "
              f"{output}")
    
    # Print failed results
    for engine, status, output, elapsed_ms, match_count in failed_results:
        color = Colors.YELLOW if status == "SKIP" else Colors.RED
        print(f"{color}{engine:<20}{Colors.NC} "
              f"{color}{status:<12}{Colors.NC} "
              f"{'--':>10}   "
              f"{'--':>6}   "
              f"{output}")
    
    print(f"{'-'*70}")
    print(f"{Colors.BOLD}Summary: {successful_tests}/{total_engines} engines succeeded{Colors.NC}")
    
    if successful_tests > 0:
        fastest = min(successful_results, key=lambda x: x[3])
        print(f"{Colors.GREEN}Fastest: {fastest[0]} ({fastest[3]:.6f} ms){Colors.NC}")
    
    print()

if __name__ == "__main__":
    main() 