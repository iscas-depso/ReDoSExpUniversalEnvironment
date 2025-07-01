#!/usr/bin/env python3
"""
Verify.py - ReDoS Attack String Verification Tool

Input: Database file (output from Gen.py), attack string file size limit (KB), match_mode
Output: Add verify_result table to database with verification results

This tool generates attack strings from ReDoS detection results and tests them
against various regex engines to measure actual performance impact.
"""

import os
import sys
import sqlite3
import base64
import json
import tempfile
import subprocess
import time
import psutil
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
import argparse

# Available engines in the benchmark suite
ENGINES = [
    "awk", "c", "cpp", "csharp", "csharp_nonbacktracking", "go", "grep", 
    "hyperscan", "java8", "java11", "nodejs14", "nodejs21", "perl", 
    "php", "python", "re2", "ruby", "rust", "srm"
]

# Global locks for thread safety
db_lock = Lock()
print_lock = Lock()

def setup_verify_table(db_path):
    """Create the verify_result table in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop the table if it exists
    cursor.execute('DROP TABLE IF EXISTS verify_result')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verify_result (
            tool TEXT NOT NULL,
            id INTEGER NOT NULL,
            engine TEXT NOT NULL,
            stdout TEXT,
            stderr TEXT,
            hyperfine_out TEXT,
            user_time REAL,
            FOREIGN KEY (id) REFERENCES regexes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_redos_attacks(db_path):
    """Get all ReDoS attacks from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ar.tool, ar.id, r.base64regex, ar.prefix, ar.infix, ar.suffix, ar.repeat_times
        FROM attack_result ar
        JOIN regexes r ON ar.id = r.id
        WHERE ar.is_redos = 1
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def decode_base64(encoded_str):
    """Decode base64 string"""
    if not encoded_str:
        return ""
    try:
        return base64.b64decode(encoded_str).decode('utf-8')
    except:
        return ""

def calculate_repeat_count(prefix, infix, suffix, max_size_kb):
    """Calculate the maximum repeat count for infix within file size limit"""
    max_size_bytes = max_size_kb * 1024
    
    prefix_len = len(prefix.encode('utf-8'))
    infix_len = len(infix.encode('utf-8'))
    suffix_len = len(suffix.encode('utf-8'))
    
    if infix_len == 0:
        return 1  # Avoid division by zero
    
    # Calculate maximum repeats that fit within size limit
    available_bytes = max_size_bytes - prefix_len - suffix_len
    max_repeats = max(1, available_bytes // infix_len)
    
    return max_repeats

def generate_attack_file(prefix, infix, suffix, repeat_count, temp_dir):
    """Generate attack string file"""
    attack_string = prefix + (infix * repeat_count) + suffix
    
    attack_file = Path(temp_dir) / "attack_string.txt"
    with open(attack_file, 'w', encoding='utf-8') as f:
        f.write(attack_string)
    
    return attack_file

def check_system_resources():
    """Check if CPU and memory usage are below 90%"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    return cpu_percent < 90 and memory_percent < 90

def wait_for_resources():
    """Wait until system resources are below 90% usage"""
    while not check_system_resources():
        with print_lock:
            print("System resources above 90%, waiting...")
        time.sleep(5)

def get_engine_executable(engine_name):
    """Get the executable path for an engine"""
    # Try different possible paths for engines
    possible_paths = [
        Path("engines") / engine_name / "bin" / "benchmark",  # Local relative path
        Path("/app/engines") / engine_name / "bin" / "benchmark",  # Docker container path
        Path("/workspace/engines") / engine_name / "bin" / "benchmark",  # Alternative Docker path
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            return str(path.absolute())
    
    # Special case for AWK
    if engine_name == "awk":
        awk_paths = [
            Path("engines") / engine_name / "benchmark.awk",
            Path("/app/engines") / engine_name / "benchmark.awk",
            Path("/workspace/engines") / engine_name / "benchmark.awk",
        ]
        for path in awk_paths:
            if path.exists():
                return str(path.absolute())
    
    return None

def run_hyperfine_engine(tool, regex_id, engine, base64_regex, attack_file, match_mode, temp_dir, timeout=5):
    """Run engine verification using hyperfine"""
    executable = get_engine_executable(engine)
    if not executable:
        return {
            "tool": tool,
            "id": regex_id,
            "engine": engine,
            "stdout": "",
            "stderr": f"Engine {engine} executable not found",
            "hyperfine_out": "",
            "user_time": 0.0
        }
    
    try:
        # Build the command to run
        if engine == "awk":
            cmd = [
                "timeout", "-k", "1s", str(timeout),
                "awk", "-f", executable, 
                base64_regex, str(attack_file), str(match_mode)
            ]
        else:
            cmd = [
                "timeout", "-k", "1s", str(timeout),
                executable,
                base64_regex, str(attack_file), str(match_mode)
            ]
        
        # Use hyperfine to benchmark the command
        hyperfine_cmd = [
            "hyperfine",
            "--min-runs", "2",
            "--max-runs", "5",
            "--show-output",
            "--export-json", f"{temp_dir}/hyperfine_{engine}.json",
            "--shell=bash",
            " ".join(f"'{arg}'" for arg in cmd)
        ]
        
        # Run hyperfine
        hyperfine_result = subprocess.run(
            hyperfine_cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Read hyperfine JSON output
        hyperfine_json_file = f"{temp_dir}/hyperfine_{engine}.json"
        hyperfine_out = ""
        user_time = 0.0
        
        if os.path.exists(hyperfine_json_file):
            with open(hyperfine_json_file, 'r') as f:
                hyperfine_out = f.read()
                
            # Parse JSON to extract user time
            try:
                hyperfine_data = json.loads(hyperfine_out)
                if "results" in hyperfine_data and len(hyperfine_data["results"]) > 0:
                    user_time = hyperfine_data["results"][0].get("user", 0.0)
            except json.JSONDecodeError:
                pass
        
        # Run the command once more to get stdout/stderr
        final_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        return {
            "tool": tool,
            "id": regex_id,
            "engine": engine,
            "stdout": final_result.stdout,
            "stderr": final_result.stderr,
            "hyperfine_out": hyperfine_out,
            "user_time": user_time
        }
        
    except subprocess.TimeoutExpired:
        return {
            "tool": tool,
            "id": regex_id,
            "engine": engine,
            "stdout": "",
            "stderr": "Timeout",
            "hyperfine_out": "",
            "user_time": 0.0
        }
    except Exception as e:
        return {
            "tool": tool,
            "id": regex_id,
            "engine": engine,
            "stdout": "",
            "stderr": str(e),
            "hyperfine_out": "",
            "user_time": 0.0
        }

def process_attack_engine_pair(args):
    """Process a single attack-engine pair"""
    tool, regex_id, base64_regex, prefix, infix, suffix, engine, max_size_kb, match_mode, db_path = args
    
    # Wait if system resources are high
    wait_for_resources()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Decode attack string components
            prefix_decoded = decode_base64(prefix)
            infix_decoded = decode_base64(infix)
            suffix_decoded = decode_base64(suffix)
            
            # Calculate repeat count based on file size limit
            repeat_count = calculate_repeat_count(prefix_decoded, infix_decoded, suffix_decoded, max_size_kb)
            
            # Generate attack file
            attack_file = generate_attack_file(prefix_decoded, infix_decoded, suffix_decoded, repeat_count, temp_dir)
            
            # Run engine verification
            result = run_hyperfine_engine(tool, regex_id, engine, base64_regex, attack_file, match_mode, temp_dir)
            
            # Store result in database
            with db_lock:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO verify_result 
                    (tool, id, engine, stdout, stderr, hyperfine_out, user_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result["tool"], result["id"], result["engine"],
                    result["stdout"], result["stderr"], result["hyperfine_out"], result["user_time"]
                ))
                conn.commit()
                conn.close()
            
            with print_lock:
                print(f"Verified: Tool {tool}, Regex {regex_id}, Engine {engine}, User time: {result['user_time']:.6f}s")
            
            return f"Tool {tool}, Regex {regex_id}, Engine {engine}: {result['user_time']:.6f}s"
            
        except Exception as e:
            with print_lock:
                print(f"Error processing tool {tool}, regex {regex_id}, engine {engine}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='ReDoS Attack String Verification Tool')
    parser.add_argument('db_file', help='Database file (output from Gen.py)')
    parser.add_argument('max_size_kb', type=int, help='Attack string file size limit in KB')
    parser.add_argument('match_mode', choices=['0', '1'], help='Match mode: 0=partial, 1=full')
    
    args = parser.parse_args()
    
    db_file = args.db_file
    max_size_kb = args.max_size_kb
    match_mode = int(args.match_mode)
    
    if not os.path.exists(db_file):
        print(f"Error: Database file {db_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Setup verify_result table
    setup_verify_table(db_file)
    
    # Get ReDoS attacks from database
    attacks = get_redos_attacks(db_file)
    if not attacks:
        print("No ReDoS attacks found in database", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(attacks)} ReDoS attacks to verify")
    
    # Calculate number of workers (80% of CPU cores)
    num_cores = multiprocessing.cpu_count()
    max_workers = max(1, int(num_cores * 0.8))
    
    print(f"Using {max_workers} workers ({num_cores} cores detected)")
    print(f"Max attack string size: {max_size_kb}KB")
    print(f"Match mode: {'full' if match_mode == 1 else 'partial'}")
    
    # Create task list
    tasks = []
    for tool, regex_id, base64_regex, prefix, infix, suffix, repeat_times in attacks:
        for engine in ENGINES:
            tasks.append((tool, regex_id, base64_regex, prefix, infix, suffix, engine, max_size_kb, match_mode, db_file))
    
    total_tasks = len(tasks)
    print(f"Total verification tasks: {total_tasks}")
    
    # Process tasks with ThreadPoolExecutor
    completed_tasks = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {executor.submit(process_attack_engine_pair, task): task for task in tasks}
        
        # Process completed tasks
        for future in as_completed(future_to_task):
            result = future.result()
            completed_tasks += 1
            
            # Progress update
            if completed_tasks % 20 == 0 or completed_tasks == total_tasks:
                elapsed_time = time.time() - start_time
                progress = (completed_tasks / total_tasks) * 100
                print(f"Progress: {completed_tasks}/{total_tasks} ({progress:.1f}%) - Elapsed: {elapsed_time:.1f}s")
    
    total_time = time.time() - start_time
    print(f"\nCompleted verification in {total_time:.1f} seconds")
    print(f"Results saved to {db_file}")
    
    # Print summary statistics
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Count verification results
    cursor.execute('SELECT COUNT(*) FROM verify_result')
    total_results = cursor.fetchone()[0]
    
    # Find slowest verifications (potential ReDoS confirmations)
    print(f"\nSummary:")
    print(f"Total verification results: {total_results}")
    
    print(f"\nTop 10 slowest verifications (potential ReDoS confirmations):")
    cursor.execute('''
        SELECT tool, id, engine, user_time 
        FROM verify_result 
        WHERE user_time > 0
        ORDER BY user_time DESC 
        LIMIT 10
    ''')
    
    for tool, regex_id, engine, user_time in cursor.fetchall():
        print(f"  {tool} - Regex {regex_id} - {engine}: {user_time:.6f}s")
    
    conn.close()

if __name__ == "__main__":
    main() 