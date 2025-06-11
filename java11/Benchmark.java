import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class Benchmark {
    public static void main(String... args) throws IOException {
        if (args.length != 3) {
            System.out.printf("Usage: java %s <base64_regex> <filename> <match_mode>%n", 
                             Benchmark.class.getSimpleName());
            System.out.println("  base64_regex: Base64-encoded regular expression");
            System.out.println("  filename: Path to the file containing text to match");
            System.out.println("  match_mode: 1 for full match, 0 for partial match");
            System.exit(1);
        }

        try {
            // Decode the base64 regex using modern Java
            var regex = decodeBase64(args[0]);
            
            // Read file content using Java 11 enhanced file I/O
            var data = readFile(args[1]);
            
            // Parse match mode
            var matchMode = parseMatchMode(args[2]);
            
            // Measure and output results
            measure(data, regex, matchMode == 1);
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    private static String decodeBase64(String base64String) {
        try {
            var decoded = Base64.getDecoder().decode(base64String);
            return new String(decoded);
        } catch (IllegalArgumentException e) {
            throw new RuntimeException("Failed to decode base64 regex: " + e.getMessage());
        }
    }

    private static String readFile(String filename) throws IOException {
        try {
            var path = Path.of(filename);
            return Files.readString(path);
        } catch (IOException e) {
            throw new IOException("Cannot open file " + filename + ": " + e.getMessage());
        }
    }

    private static int parseMatchMode(String matchModeStr) {
        try {
            var matchMode = Integer.parseInt(matchModeStr);
            if (matchMode != 0 && matchMode != 1) {
                throw new IllegalArgumentException("match_mode must be 0 or 1");
            }
            return matchMode;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("match_mode must be 0 or 1");
        }
    }

    private static void measure(String data, String patternStr, boolean fullMatch) {
        var startTime = Instant.now();

        try {
            var pattern = Pattern.compile(patternStr);
            var count = 0;

            if (fullMatch) {
                // Full match: entire text must match the regex
                var matcher = pattern.matcher(data);
                if (matcher.matches()) {
                    count = 1;
                } else {
                    count = 0;
                }
            } else {
                // Partial match: find all matches in the text
                var matcher = pattern.matcher(data);
                while (matcher.find()) {
                    count++;
                }
            }

            var endTime = Instant.now();
            var duration = Duration.between(startTime, endTime);
            var elapsedMs = duration.toNanos() / 1_000_000.0;

            System.out.printf("%.6f - %d%n", elapsedMs, count);

        } catch (Exception e) {
            System.err.println("Error: Failed to compile regex: " + e.getMessage());
            System.exit(1);
        }
    }
} 