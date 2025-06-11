using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Diagnostics;
using System.Globalization;

class Benchmark
{
    static void Main(string[] args)
    {
        if (args.Length != 3)
        {
            Console.WriteLine("Usage: {0} <base64_regex> <filename> <match_mode>", 
                System.Reflection.Assembly.GetExecutingAssembly().GetName().Name);
            Console.WriteLine("  base64_regex: Base64-encoded regular expression");
            Console.WriteLine("  filename: Path to the file containing text to match");
            Console.WriteLine("  match_mode: 1 for full match, 0 for partial match");
            Environment.Exit(1);
        }

        // Decode the base64 regex
        string regex;
        try
        {
            regex = DecodeBase64(args[0]);
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Error: Failed to decode base64 regex: {0}", e.Message);
            Environment.Exit(1);
            return;
        }

        // Read file content
        string data = ReadFile(args[1]);

        // Parse match mode
        int matchMode;
        if (!int.TryParse(args[2], out matchMode) || (matchMode != 0 && matchMode != 1))
        {
            Console.Error.WriteLine("Error: match_mode must be 0 or 1");
            Environment.Exit(1);
        }

        // Measure and output results
        Measure(data, regex, matchMode);
    }

    static string DecodeBase64(string base64String)
    {
        try
        {
            byte[] data = Convert.FromBase64String(base64String);
            return Encoding.UTF8.GetString(data);
        }
        catch (Exception)
        {
            throw new ArgumentException("Invalid base64 string");
        }
    }

    static string ReadFile(string filename)
    {
        try
        {
            return File.ReadAllText(filename);
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Error: Cannot open file {0}: {1}", filename, e.Message);
            Environment.Exit(1);
            return "";
        }
    }

    static void Measure(string data, string pattern, int fullMatch)
    {
        Stopwatch stopwatch = Stopwatch.StartNew();
        int count = 0;

        try
        {
            if (fullMatch == 1)
            {
                // Full match: entire text must match the regex
                if (Regex.IsMatch(data, "^(" + pattern + ")$"))
                {
                    count = 1;
                }
            }
            else
            {
                // Partial match: find all matches in the text
                MatchCollection matches = Regex.Matches(data, pattern);
                count = matches.Count;
            }
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Error: Failed to process regex: {0}", e.Message);
            Environment.Exit(1);
        }

        stopwatch.Stop();
        
        double elapsedMs = stopwatch.Elapsed.TotalMilliseconds;
        Console.WriteLine("{0:F6} - {1}", elapsedMs, count);
    }
}
