#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <cstdlib>
#include <vector>
#include <re2/re2.h>

// Simple base64 decoder implementation
std::string base64_decode(const std::string& input) {
    const std::string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string result;
    int val = 0, valb = -8;
    
    for (unsigned char c : input) {
        if (c == '=') break;  // Padding character
        
        size_t pos = chars.find(c);
        if (pos == std::string::npos) continue;  // Skip invalid characters
        
        val = (val << 6) + pos;
        valb += 6;
        if (valb >= 0) {
            result.push_back(char((val >> valb) & 0xFF));
            valb -= 8;
        }
    }
    
    return result;
}

std::string read_file(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "Error: Cannot open file " << filename << std::endl;
        exit(1);
    }
    
    std::string content((std::istreambuf_iterator<char>(file)),
                       std::istreambuf_iterator<char>());
    file.close();
    
    return content;
}

void measure(const std::string& data, const std::string& pattern, int full_match) {
    int count = 0;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    RE2 regex(pattern);
    if (!regex.ok()) {
        std::cerr << "Error: Failed to compile regex: " << regex.error() << std::endl;
        exit(1);
    }
    
    if (full_match) {
        // Full match: entire text must match the regex
        if (RE2::FullMatch(data, regex)) {
            count = 1;
        }
    } else {
        // Partial match: find all matches in the text
        re2::StringPiece input(data);
        
        while (RE2::FindAndConsume(&input, regex)) {
            count++;
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    double elapsed_ms = elapsed.count() / 1e6;
    
    printf("%.6f - %d\n", elapsed_ms, count);
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cout << "Usage: " << argv[0] << " <base64_regex> <filename> <match_mode>" << std::endl;
        std::cout << "  base64_regex: Base64-encoded regular expression" << std::endl;
        std::cout << "  filename: Path to the file containing text to match" << std::endl;
        std::cout << "  match_mode: 1 for full match, 0 for partial match" << std::endl;
        exit(1);
    }
    
    // Decode the base64 regex
    std::string regex = base64_decode(argv[1]);
    
    // Read file content
    std::string data = read_file(argv[2]);
    
    // Parse match mode
    int match_mode = std::atoi(argv[3]);
    if (match_mode != 0 && match_mode != 1) {
        std::cerr << "Error: match_mode must be 0 or 1" << std::endl;
        exit(1);
    }
    
    // Measure and output results
    measure(data, regex, match_mode);
    
    return 0;
} 