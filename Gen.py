#!/usr/bin/env python3
"""
Gen.py - ReDoS Attack Generation and Testing Tool

Input: A txt file where each line is a regular expression
Output: A sqlite database file with regexes and attack_result tables

This tool processes regular expressions through multiple ReDoS detection tools
and stores the results in a database for analysis.
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

# Available tools in the tools directory
TOOLS = ['rescue', 'regexstatic', 'regexploit', 'rengar', 'regulator', 'redoshunter']

# Global locks for thread safety
db_lock = Lock()
print_lock = Lock()

def setup_database(db_path):
    """Create the sqlite database with required tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create regexes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regexes (
            id INTEGER PRIMARY KEY,
            regex TEXT NOT NULL,
            base64regex TEXT NOT NULL
        )
    ''')
    
    # Create attack_result table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attack_result (
            tool TEXT NOT NULL,
            id INTEGER NOT NULL,
            is_redos BOOLEAN NOT NULL,
            prefix TEXT,
            infix TEXT,
            suffix TEXT,
            repeat_times INTEGER,
            elapsed_ms INTEGER,
            full_json TEXT,
            hyperfine_out TEXT,
            FOREIGN KEY (id) REFERENCES regexes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def load_regexes(file_path, db_path):
    """Load regexes from file into database"""
    regexes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for line_num, line in enumerate(lines, 1):
            regex = line.strip()
            if regex:  # Skip empty lines
                base64_regex = base64.b64encode(regex.encode('utf-8')).decode('utf-8')
                cursor.execute(
                    'INSERT OR REPLACE INTO regexes (id, regex, base64regex) VALUES (?, ?, ?)',
                    (line_num, regex, base64_regex)
                )
                regexes.append((line_num, regex, base64_regex))
        
        conn.commit()
        conn.close()
        
        with print_lock:
            print(f"Loaded {len(regexes)} regexes from {file_path}")
        
        return regexes
        
    except Exception as e:
        print(f"Error loading regexes: {e}", file=sys.stderr)
        return []

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

def run_hyperfine_tool(tool, base64_regex, temp_dir, timeout=600):
    """Run a tool using hyperfine for benchmarking"""
    # Try different possible tool paths
    possible_paths = [
        Path("tools") / tool / "run.py",  # Local relative path
        Path("/app/tools") / tool / "run.py",  # Docker container path
        Path("/workspace/tools") / tool / "run.py",  # Alternative Docker path
    ]
    
    tool_path = None
    for path in possible_paths:
        if path.exists():
            tool_path = path
            break
    
    if tool_path is None:
        return None, f"Tool {tool} not found in any of: {', '.join(str(p) for p in possible_paths)}"
    
    # Create temp output file
    output_file = Path(temp_dir) / f"{tool}_output.json"
    
    # Build the command to run with timeout
    cmd = [
        "timeout", "-k", "1s", str(timeout),
        "python3", str(tool_path.absolute()),
        base64_regex,
        str(output_file.absolute())
    ]
    
    # Use hyperfine to benchmark the command (minimum 2 runs)
    hyperfine_cmd = [
        "hyperfine",
        "--min-runs", "2",
        "--max-runs", "5",
        "--export-json", f"{temp_dir}/hyperfine_{tool}.json",
        "--shell=bash",
        " ".join(f"'{arg}'" for arg in cmd)
    ]
    
    try:
        # Run hyperfine
        hyperfine_result = subprocess.run(
            hyperfine_cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path.cwd()
        )
        
        # Read hyperfine JSON output
        hyperfine_json_file = f"{temp_dir}/hyperfine_{tool}.json"
        hyperfine_out = ""
        if os.path.exists(hyperfine_json_file):
            with open(hyperfine_json_file, 'r') as f:
                hyperfine_out = f.read()
        
        # Run the tool one final time to get the actual result
        final_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Read tool output
        if final_result.returncode == 0 and output_file.exists():
            with open(output_file, 'r') as f:
                tool_output = json.load(f)
            return tool_output, hyperfine_out
        else:
            # Tool failed, create default output
            default_output = {
                "elapsed_ms": 0,
                "is_redos": False,
                "error": final_result.stderr
            }
            return default_output, hyperfine_out
            
    except subprocess.TimeoutExpired:
        default_output = {
            "elapsed_ms": timeout * 1000,
            "is_redos": False,
            "error": "Timeout"
        }
        return default_output, ""
    except Exception as e:
        default_output = {
            "elapsed_ms": 0,
            "is_redos": False,
            "error": str(e)
        }
        return default_output, ""

def process_regex_tool_pair(args):
    """Process a single regex-tool pair"""
    regex_id, regex, base64_regex, tool, db_path, timeout = args
    
    # Wait if system resources are high
    wait_for_resources()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            tool_output, hyperfine_out = run_hyperfine_tool(tool, base64_regex, temp_dir, timeout)
            
            if tool_output is None:
                return None
            
            # Extract fields from tool output
            is_redos = tool_output.get('is_redos', False)
            prefix = tool_output.get('prefix', '')
            infix = tool_output.get('infix', '')
            suffix = tool_output.get('suffix', '')
            repeat_times = tool_output.get('repeat_times', -1)
            elapsed_ms = tool_output.get('elapsed_ms', 0)
            
            # Store result in database
            with db_lock:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO attack_result 
                    (tool, id, is_redos, prefix, infix, suffix, repeat_times, elapsed_ms, full_json, hyperfine_out)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tool, regex_id, is_redos, prefix, infix, suffix, repeat_times, elapsed_ms,
                    json.dumps(tool_output), hyperfine_out
                ))
                conn.commit()
                conn.close()
            
            with print_lock:
                status = "ReDoS" if is_redos else "Safe"
                print(f"Processed: Regex {regex_id}, Tool {tool}, Result: {status}")
            
            return f"Regex {regex_id}, Tool {tool}: {status}"
            
        except Exception as e:
            with print_lock:
                print(f"Error processing regex {regex_id} with tool {tool}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='ReDoS Attack Generation and Testing Tool')
    parser.add_argument('input_file', help='Input txt file with regexes (one per line)')
    parser.add_argument('output_db', help='Output sqlite database file')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout per tool run in seconds (default: 600)')
    
    args = parser.parse_args()
    
    input_file = args.input_file
    output_db = args.output_db
    timeout = args.timeout
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Setup database
    setup_database(output_db)
    
    # Load regexes
    regexes = load_regexes(input_file, output_db)
    if not regexes:
        print("No regexes loaded, exiting", file=sys.stderr)
        sys.exit(1)
    
    # Calculate number of workers (80% of CPU cores)
    num_cores = multiprocessing.cpu_count()
    max_workers = max(1, int(num_cores * 0.8))
    
    print(f"Using {max_workers} workers ({num_cores} cores detected)")
    print(f"Processing {len(regexes)} regexes with {len(TOOLS)} tools")
    print(f"Total tasks: {len(regexes) * len(TOOLS)}")
    
    # Create task list
    tasks = []
    for regex_id, regex, base64_regex in regexes:
        for tool in TOOLS:
            tasks.append((regex_id, regex, base64_regex, tool, output_db, timeout))
    
    # Process tasks with ThreadPoolExecutor
    completed_tasks = 0
    total_tasks = len(tasks)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {executor.submit(process_regex_tool_pair, task): task for task in tasks}
        
        # Process completed tasks
        for future in as_completed(future_to_task):
            result = future.result()
            completed_tasks += 1
            
            # Progress update
            if completed_tasks % 10 == 0 or completed_tasks == total_tasks:
                elapsed_time = time.time() - start_time
                progress = (completed_tasks / total_tasks) * 100
                print(f"Progress: {completed_tasks}/{total_tasks} ({progress:.1f}%) - Elapsed: {elapsed_time:.1f}s")
    
    total_time = time.time() - start_time
    print(f"\nCompleted processing all tasks in {total_time:.1f} seconds")
    print(f"Results saved to {output_db}")
    
    # Print summary statistics
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # Count total results
    cursor.execute('SELECT COUNT(*) FROM attack_result')
    total_results = cursor.fetchone()[0]
    
    # Count ReDoS detections by tool
    print(f"\nSummary:")
    print(f"Total results: {total_results}")
    
    for tool in TOOLS:
        cursor.execute('SELECT COUNT(*) FROM attack_result WHERE tool = ? AND is_redos = 1', (tool,))
        redos_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM attack_result WHERE tool = ?', (tool,))
        total_count = cursor.fetchone()[0]
        print(f"{tool}: {redos_count}/{total_count} ReDoS detected")
    
    conn.close()

if __name__ == "__main__":
    main() 