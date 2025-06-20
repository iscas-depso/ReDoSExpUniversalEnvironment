using System;
using System.IO;
using System.Diagnostics;
using System.Text;
using Microsoft.SRM;

class Benchmark
{
    static void Main(string[] args)
    {
        if (args.Length != 3)
        {
            Console.WriteLine("Usage: benchmark <base64_regex> <filename> <match_mode>");
            Console.WriteLine("  base64_regex: Base64-encoded regular expression");
            Console.WriteLine("  filename: Path to file containing text to match");
            Console.WriteLine("  match_mode: 0 for partial match, 1 for full match");
            Environment.Exit(1);
        }

        string base64Regex = args[0];
        string filename = args[1];
        string matchModeStr = args[2];

        // Parse match mode
        if (!int.TryParse(matchModeStr, out int matchMode) || (matchMode != 0 && matchMode != 1))
        {
            Console.WriteLine("Error: match_mode must be 0 (partial) or 1 (full)");
            Environment.Exit(1);
        }

        // Decode Base64 regex
        string regex = "";
        try
        {
            byte[] data = Convert.FromBase64String(base64Regex);
            regex = Encoding.UTF8.GetString(data);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error decoding Base64 regex: {ex.Message}");
            Environment.Exit(1);
        }

        // Read input file
        string text = "";
        try
        {
            text = File.ReadAllText(filename, Encoding.UTF8);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error reading file '{filename}': {ex.Message}");
            Environment.Exit(1);
        }

        // Prepare regex pattern based on match mode
        string pattern = regex;
        if (matchMode == 1)
        {
            // Full match: anchor the pattern to match entire string
            if (!pattern.StartsWith("^"))
                pattern = "^" + pattern;
            if (!pattern.EndsWith("$"))
                pattern = pattern + "$";
        }

        // Measure regex matching performance
        Stopwatch stopwatch = Stopwatch.StartNew();
        
        int matchCount = 0;
        try
        {
            var r = new Regex(pattern);
            
            if (matchMode == 0)
            {
                // Partial matching - count all matches
                var matches = r.Matches(text);
                matchCount = matches.Count;
            }
            else
            {
                // Full matching - check if entire string matches
                var matches = r.Matches(text);
                matchCount = matches.Count > 0 ? 1 : 0;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error in regex matching: {ex.Message}");
            Environment.Exit(1);
        }

        stopwatch.Stop();
        double elapsedMs = stopwatch.Elapsed.TotalMilliseconds;

        // Output in required format: {elapsed_time:.6f} - {match_count}
        Console.WriteLine($"{elapsedMs:F6} - {matchCount}");
    }
}
