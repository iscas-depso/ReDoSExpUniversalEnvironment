#!/usr/bin/env ruby

require 'base64'

def read_file(filename)
  begin
    File.read(filename)
  rescue Errno::ENOENT
    $stderr.puts "Error: Cannot open file #{filename}"
    exit 1
  rescue => e
    $stderr.puts "Error: Failed to read file #{filename}: #{e.message}"
    exit 1
  end
end

def measure(data, pattern, full_match)
  start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  
  count = 0
  
  begin
    if full_match
      # Full match: entire text must match the regex
      regex = Regexp.new("\\A#{pattern}\\z", Regexp::MULTILINE)
      count = data.match?(regex) ? 1 : 0
    else
      # Partial match: count all matches in the text
      regex = Regexp.new(pattern)
      count = data.scan(regex).size
    end
  rescue RegexpError => e
    $stderr.puts "Error: Invalid regex pattern: #{e.message}"
    exit 1
  end
  
  elapsed = (Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000  # Convert to milliseconds
  
  printf("%.6f - %d\n", elapsed, count)
end

def main
  if ARGV.size != 3
    puts "Usage: #{$0} <base64_regex> <filename> <match_mode>"
    puts "  base64_regex: Base64-encoded regular expression"
    puts "  filename: Path to the file containing text to match"
    puts "  match_mode: 1 for full match, 0 for partial match"
    exit 1
  end
  
  base64_regex = ARGV[0]
  filename = ARGV[1]
  match_mode = ARGV[2]
  
  # Decode the base64 regex
  begin
    regex = Base64.strict_decode64(base64_regex)
  rescue ArgumentError => e
    $stderr.puts "Error: Failed to decode base64 regex: #{e.message}"
    exit 1
  end
  
  # Validate match mode
  unless match_mode == '0' || match_mode == '1'
    $stderr.puts "Error: match_mode must be 0 or 1"
    exit 1
  end
  
  # Read file content
  data = read_file(filename)
  
  # Measure and output results
  measure(data, regex, match_mode == '1')
end

if __FILE__ == $0
  main
end