import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
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
            // Decode the base64 regex
            String regex = decodeBase64(args[0]);
            
            // Read file content
            String data = readFile(args[1]);
            
            // Parse match mode
            int matchMode = parseMatchMode(args[2]);
            
            // Measure and output results
            measure(data, regex, matchMode == 1);
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    private static String decodeBase64(String base64String) {
        try {
            byte[] decoded = Base64.getDecoder().decode(base64String);
            return new String(decoded);
        } catch (IllegalArgumentException e) {
            throw new RuntimeException("Failed to decode base64 regex: " + e.getMessage());
        }
    }

    private static String readFile(String filename) throws IOException {
        try {
            return new String(Files.readAllBytes(Paths.get(filename)));
        } catch (IOException e) {
            throw new IOException("Cannot open file " + filename + ": " + e.getMessage());
        }
    }

    private static int parseMatchMode(String matchModeStr) {
        try {
            int matchMode = Integer.parseInt(matchModeStr);
            if (matchMode != 0 && matchMode != 1) {
                throw new IllegalArgumentException("match_mode must be 0 or 1");
            }
            return matchMode;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("match_mode must be 0 or 1");
        }
    }

    private static void measure(String data, String patternStr, boolean fullMatch) {
        long startTime = System.nanoTime();

        try {
            Pattern pattern = Pattern.compile(patternStr);
            int count = 0;

            if (fullMatch) {
                // Full match: entire text must match the regex
                Matcher matcher = pattern.matcher(data);
                if (matcher.matches()) {
                    count = 1;
                } else {
                    count = 0;
                }
            } else {
                // Partial match: find all matches in the text
                Matcher matcher = pattern.matcher(data);
                while (matcher.find()) {
                    count++;
                }
            }

            long elapsed = System.nanoTime() - startTime;
            double elapsedMs = elapsed / 1e6;

            System.out.printf("%.6f - %d%n", elapsedMs, count);

        } catch (Exception e) {
            System.err.println("Error: Failed to compile regex: " + e.getMessage());
            System.exit(1);
        }
    }
}
