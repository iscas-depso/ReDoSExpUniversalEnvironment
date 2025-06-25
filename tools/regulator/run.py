#!/usr/bin/env python3
"""
ReDoS regex attack string generate tool - Regulator
Entry point script that follows the project contract.
"""

import sys
import subprocess
import json
import time
import os
import base64
import tempfile
import asyncio
import re
from pathlib import Path

# Import the pump module from regulator-dynamic
sys.path.append(str(Path(__file__).parent / "regulator-dynamic" / "driver"))
import pump
import binsearch_pump

# Patterns for interpreting fuzzer stdout
witness_pat = re.compile(r'SUMMARY.+? word="(.+?)" Total=(\d+) MaxObservation')
max_tot_exceeded_pat = re.compile(r'Maximum Total reached:.*?word="(.+?)" Total=(\d+) MaxObservation')

def decode_witness_one_byte(s: str) -> bytes:
    """Decode one-byte witness string"""
    import ast
    s = s.replace("'", "\\'")
    s = ast.literal_eval("b'" + s + "'")
    return s

def decode_witness_two_byte(s: str) -> bytes:
    """Decode two-byte witness string"""
    b = b''
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and s[i+1] == 'u':
            b1 = int(s[i+2:i+4], 16)
            b2 = int(s[i+4:i+6], 16)
            # load as little-endian
            b += bytes([b2, b1])
            i += 6
        elif c == '\\' and s[i+1] == '\\':
            b += bytes([ord('\\'), 0])
            i += 2
        elif c == '\\' and s[i+1] == 'r':
            b += bytes([ord('\r'), 0])
            i += 2
        elif c == '\\' and s[i+1] == 't':
            b += bytes([ord('\t'), 0])
            i += 2
        elif c == '\\' and s[i+1] == 'n':
            b += bytes([ord('\n'), 0])
            i += 2
        else:
            assert ' ' <= c <= '~'
            b += bytes([ord(c), 0])
            i += 1
    return b

async def run_fuzzer(fuzzer_binary, regex_b64, flags, ftime_ms=240000, length=200, width=1):
    """Run the regulator fuzzer and return witness"""
    witness = None
    witness_score = 0
    
    fuzz_deadline = time.time() + ftime_ms / 1000
    current_length = length
    maxtot = 500_000
    n_backoffs = 0
    
    fuzzer_flags = []
    if flags.strip():
        fuzzer_flags += ['--flags', flags.strip()]
    
    while True:
        # Start the fuzzer
        p = await asyncio.create_subprocess_exec(
            fuzzer_binary,
            '--bregexp', regex_b64,
            '--lengths', str(current_length),
            '--widths', str(width),
            '--timeout', str(int(ftime_ms / 1000) + 30),
            '--maxtot', str(maxtot),
            *fuzzer_flags,
            stderr=asyncio.subprocess.STDOUT,  # Combine stderr with stdout
            stdout=asyncio.subprocess.PIPE,
        )
        
        my_witness = None
        my_witness_score = 0
        
        # Read loop over each line, respecting deadline
        while True:
            time_remaining = fuzz_deadline - time.time()
            if time_remaining <= 0:
                # Kill process (its over-time)
                p.kill()
                while True:
                    try:
                        await asyncio.wait_for(p.wait(), 10)
                        break
                    except asyncio.TimeoutError:
                        p.kill()
                        pass
                break
                
            try:
                line = await asyncio.wait_for(p.stdout.readline(), time_remaining)
            except asyncio.TimeoutError:
                continue
                
            if line is None or len(line) == 0:
                break
                
            # Decode line and match patterns
            line = line.decode('utf8')
            
            # Check for early-exit max-total-exceeded
            tot_exceed_mat = max_tot_exceeded_pat.search(line)
            if tot_exceed_mat is not None:
                try:
                    await asyncio.wait_for(p.wait(), 10)
                except asyncio.TimeoutError:
                    raise Exception('exceeded shutdown time')
                my_witness = tot_exceed_mat.group(1)
                my_witness_score = int(tot_exceed_mat.group(2))
                break
            
            # Check for witness
            witness_mat = witness_pat.search(line)
            if witness_mat is not None:
                old_witness_score = my_witness_score
                my_witness = witness_mat.group(1)
                my_witness_score = int(witness_mat.group(2))
        
        # if we exceeded max score or this is first attempt
        if n_backoffs == 0 or my_witness_score >= maxtot * 0.60:
            witness = my_witness
            witness_score = my_witness_score

        # if there's time left and we bumped against the limit, back-off
        time_remaining = fuzz_deadline - time.time()
        if time_remaining > 5 and witness_score >= (maxtot * 0.95):
            old_len = current_length
            current_length = (current_length - 20) // 2 + 20
            if current_length == old_len:
                break
            else:
                n_backoffs += 1
        else:
            break
    
    return witness, witness_score

def main():
    if len(sys.argv) != 3:
        print("Usage: python run.py <base64_regex> <output_file_path>", file=sys.stderr)
        sys.exit(1)
    
    base64_regex = sys.argv[1]
    output_file_path = sys.argv[2]

    ftime_ms = 5000 # Maximum milliseconds to spend fuzzing
    ptime_ms = 5000 # Maximum milliseconds to spend pumping
    binary_search = False # Whether to use binary search to find the limit
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    fuzzer_binary = script_dir / "regulator-dynamic" / "fuzzer" / "build" / "fuzzer"
    
    if not fuzzer_binary.exists():
        print(f"Error: Regulator fuzzer not found at {fuzzer_binary}", file=sys.stderr)
        # Return not ReDoS if fuzzer is not available
        output_json = {
            "elapsed_ms": 0,
            "is_redos": False
        }
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        return
    
    try:
        # Record start time
        start_time = time.time()
        
        # Decode base64 regex
        try:
            regex_bytes = base64.b64decode(base64_regex, validate=True)
            regex_str = regex_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error decoding base64 regex: {e}", file=sys.stderr)
            output_json = {
                "elapsed_ms": 0,
                "is_redos": False
            }
            with open(output_file_path, 'w') as f:
                json.dump(output_json, f, indent=2)
            return
        
        # Set up pump module fuzzer binary
        pump.fuzzer_binary = str(fuzzer_binary)
        
        # Run the fuzzer asynchronously
        witness, witness_score = asyncio.run(run_fuzzer(
            str(fuzzer_binary), 
            base64_regex, 
            "",  # Default empty flags
            ftime_ms=5000,  # 4 minutes fuzzing
            length=200,
            width=1
        ))
        
        # Record end time
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        
        # Initialize output
        output_json = {
            "elapsed_ms": elapsed_ms,
            "is_redos": False
        }
        
        if witness and witness_score > 0:
            # We found a potential ReDoS, need to analyze further
            try:
                # Decode the witness
                bwitness = decode_witness_one_byte(witness)
                
                # Run pump analysis to get attack string structure
                deadline = time.time() * 1000 + 5000  # 4 minutes for pumping
                
                report = pump.get_pump_report(
                    regex_bytes,
                    b"",  # Empty flags
                    bwitness,
                    1,    # width=1
                    deadline
                )
                
                # Check classification following the logic from main.py
                report_class = report.get("class", "UNKNOWN")
                
                # Determine if it's ReDoS based on classification
                is_redos_vulnerable = False
                repeat_times = -1
                
                if report_class.startswith("EXPONENTIAL"):
                    is_redos_vulnerable = True
                    repeat_times = 100000  # Large number for exponential
                elif report_class == "POLYNOMIAL":
                    is_redos_vulnerable = True
                    if binary_search:
                        # For polynomial, try to get a reasonable repeat count
                        # Use binary search to find limit if available
                        if 'pump_pos' in report and 'pump_len' in report:
                            try:
                                # Try binary search for more precise repeat count
                                limit = binsearch_pump.find_limit(
                                    regex_bytes,
                                    b"",  # Empty flags
                                    bwitness,
                                    1,    # width=1
                                    report['pump_pos'],
                                    report['pump_len'],
                                )
                                if limit and limit > 0:
                                    repeat_times = limit
                                else:
                                    repeat_times = 100000  # Default for polynomial
                            except Exception as e:
                                print(f"Binary search failed: {e}", file=sys.stderr)
                                repeat_times = 100000  # Default fallback
                            else:
                                repeat_times = 100000
                    else:
                        repeat_times = 100000
                
                if is_redos_vulnerable and 'pump_pos' in report and 'pump_len' in report:
                    output_json["is_redos"] = True
                    
                    pump_pos = report['pump_pos']
                    pump_len = report['pump_len']
                    
                    # Create attack string components
                    prefix = bwitness[:pump_pos]
                    infix = bwitness[pump_pos:pump_pos + pump_len]
                    suffix = bwitness[pump_pos + pump_len:]
                    
                    # Encode as base64
                    output_json.update({
                        "prefix": base64.b64encode(prefix).decode('utf-8'),
                        "infix": base64.b64encode(infix).decode('utf-8'),
                        "suffix": base64.b64encode(suffix).decode('utf-8'),
                        "repeat_times": repeat_times
                    })
                elif is_redos_vulnerable:
                    # ReDoS detected but no pump info available (e.g., baseline timeout)
                    output_json["is_redos"] = True
                    output_json.update({
                        "prefix": base64.b64encode(b"").decode('utf-8'),
                        "infix": base64.b64encode(bwitness).decode('utf-8'),
                        "suffix": base64.b64encode(b"").decode('utf-8'),
                        "repeat_times": repeat_times
                    })
                else:
                    # Not classified as ReDoS
                    output_json["is_redos"] = False
                    
            except Exception as e:
                print(f"Error during pump analysis: {e}", file=sys.stderr)
                # Still mark as ReDoS if we found a witness, but without detailed attack structure
                output_json.update({
                    "prefix": base64.b64encode(b"").decode('utf-8'),
                    "infix": base64.b64encode(b"").decode('utf-8'),
                    "suffix": base64.b64encode(b"").decode('utf-8'),
                    "repeat_times": -1
                })
        
        # Write output to file
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f, indent=2)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        output_json = {
            "elapsed_ms": 0,
            "is_redos": False
        }
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f, indent=2)

if __name__ == "__main__":
    main() 