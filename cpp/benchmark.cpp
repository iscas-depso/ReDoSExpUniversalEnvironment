#define _POSIX_C_SOURCE 199309L

#include <chrono>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <string>
#include <vector>
#include <stdexcept>
#include <cstdlib>
#include <boost/regex.hpp>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>

std::string base64_decode(const std::string& input) {
    BIO *bio, *b64;
    int decode_length = input.length();
    std::vector<char> buffer(decode_length + 1);
    
    bio = BIO_new_mem_buf(input.c_str(), -1);
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_push(b64, bio);
    
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    int output_length = BIO_read(bio, buffer.data(), decode_length);
    buffer[output_length] = '\0';
    
    BIO_free_all(bio);
    
    return std::string(buffer.data(), output_length);
}

std::string read_file(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << "Error: Cannot open file " << filename << std::endl;
        std::exit(1);
    }
    
    return std::string(std::istreambuf_iterator<char>(file), 
                      std::istreambuf_iterator<char>());
}

void measure(const std::string& data, const std::string& pattern, int full_match) {
    using clock = std::chrono::high_resolution_clock;
    const auto start = clock::now();
    
    unsigned count = 0;
    
    try {
        if (full_match) {
            // Full match: entire text must match the regex
            const REGEX_NAMESPACE::regex re(pattern);
            if (REGEX_NAMESPACE::regex_match(data, re)) {
                count = 1;
            }
        } else {
            // Partial match: find all matches in the text
            const REGEX_NAMESPACE::regex re(pattern);
            for (REGEX_NAMESPACE::sregex_token_iterator it(data.cbegin(), data.cend(), re), end{}; 
                 it != end; ++it) {
                count++;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: Failed to process regex: " << e.what() << std::endl;
        std::exit(1);
    }
    
    const auto end = clock::now();
    const double elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count() * 1e-6;
    std::cout << std::fixed << std::setprecision(6) << elapsed << " - " << count << std::endl;
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cout << "Usage: " << argv[0] << " <base64_regex> <filename> <match_mode>" << std::endl;
        std::cout << "  base64_regex: Base64-encoded regular expression" << std::endl;
        std::cout << "  filename: Path to the file containing text to match" << std::endl;
        std::cout << "  match_mode: 1 for full match, 0 for partial match" << std::endl;
        return 1;
    }
    
    // Decode the base64 regex
    std::string regex;
    try {
        regex = base64_decode(argv[1]);
    } catch (const std::exception& e) {
        std::cerr << "Error: Failed to decode base64 regex: " << e.what() << std::endl;
        return 1;
    }
    
    // Read file content
    std::string data = read_file(argv[2]);
    
    // Parse match mode
    int match_mode = std::atoi(argv[3]);
    if (match_mode != 0 && match_mode != 1) {
        std::cerr << "Error: match_mode must be 0 or 1" << std::endl;
        return 1;
    }
    
    // Measure and output results
    measure(data, regex, match_mode);
    
    return 0;
}
