use std::env;
use std::fs;
use std::time::Instant;
use std::process;
use regex::Regex;
use base64;

fn read_file(filename: &str) -> Result<String, Box<dyn std::error::Error>> {
    match fs::read_to_string(filename) {
        Ok(content) => Ok(content),
        Err(e) => {
            eprintln!("Error: Cannot open file {}: {}", filename, e);
            process::exit(1);
        }
    }
}

fn measure(data: &str, pattern: &str, full_match: bool) -> Result<(), Box<dyn std::error::Error>> {
    let start = Instant::now();
    
    let count = if full_match {
        // Full match: entire text must match the regex
        let full_pattern = format!("^{}$", pattern);
        match Regex::new(&full_pattern) {
            Ok(regex) => {
                if regex.is_match(data) { 1 } else { 0 }
            }
            Err(e) => {
                eprintln!("Error: Invalid regex pattern: {}", e);
                process::exit(1);
            }
        }
    } else {
        // Partial match: count all matches in the text
        match Regex::new(pattern) {
            Ok(regex) => regex.find_iter(data).count(),
            Err(e) => {
                eprintln!("Error: Invalid regex pattern: {}", e);
                process::exit(1);
            }
        }
    };
    
    let elapsed = start.elapsed();
    let elapsed_ms = elapsed.as_secs_f64() * 1000.0;  // Convert to milliseconds
    
    println!("{:.6} - {}", elapsed_ms, count);
    
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    if args.len() != 4 {
        println!("Usage: {} <base64_regex> <filename> <match_mode>", args[0]);
        println!("  base64_regex: Base64-encoded regular expression");
        println!("  filename: Path to the file containing text to match");
        println!("  match_mode: 1 for full match, 0 for partial match");
        process::exit(1);
    }
    
    let base64_regex = &args[1];
    let filename = &args[2];
    let match_mode = &args[3];
    
    // Decode the base64 regex
    let regex = match base64::decode(base64_regex) {
        Ok(decoded) => match String::from_utf8(decoded) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Error: Failed to decode base64 regex: {}", e);
                process::exit(1);
            }
        },
        Err(e) => {
            eprintln!("Error: Failed to decode base64 regex: {}", e);
            process::exit(1);
        }
    };
    
    // Validate match mode
    let full_match = match match_mode.as_str() {
        "0" => false,
        "1" => true,
        _ => {
            eprintln!("Error: match_mode must be 0 or 1");
            process::exit(1);
        }
    };
    
    // Read file content
    let data = read_file(filename)?;
    
    // Measure and output results
    measure(&data, &regex, full_match)?;
    
    Ok(())
}
