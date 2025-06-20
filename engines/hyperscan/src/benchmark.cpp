#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <memory>

#include <hs/hs.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>

// Global variables for match counting
static int match_count = 0;
static bool full_match_mode = false;
static size_t text_length = 0;

// Base64 decoding function
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

// Read file contents
std::string read_file(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary | std::ios::ate);
    if (!file) {
        std::cerr << "Error: Cannot open file " << filename << std::endl;
        std::exit(1);
    }
    
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<char> buffer(size);
    if (!file.read(buffer.data(), size)) {
        std::cerr << "Error: Failed to read file" << std::endl;
        std::exit(1);
    }
    
    return std::string(buffer.begin(), buffer.end());
}

// Match callback function
static int on_match(unsigned int id, unsigned long long from, unsigned long long to,
                   unsigned int flags, void *context) {
    if (full_match_mode) {
        // For full match, check if the match covers the entire text
        if (from == 0 && to == text_length) {
            match_count = 1;
        }
    } else {
        // For partial match, count all matches
        match_count++;
    }
    return 0; // Continue matching
}

// Measure regex performance using Hyperscan
void measure(const std::string& data, const std::string& pattern, int full_match) {
    match_count = 0;
    full_match_mode = (full_match == 1);
    text_length = data.length();
    
    auto start = std::chrono::high_resolution_clock::now();
    
    // Compile the Hyperscan pattern
    hs_database_t *database = nullptr;
    hs_compile_error_t *compile_err = nullptr;
    
    unsigned int flags = 0;
    if (full_match) {
        // For full match, we need start-of-match reporting
        flags = HS_FLAG_SOM_LEFTMOST;
    }
    
    if (hs_compile(pattern.c_str(), flags, HS_MODE_BLOCK, nullptr, &database, &compile_err) != HS_SUCCESS) {
        std::cerr << "Error: Failed to compile pattern: ";
        if (compile_err) {
            std::cerr << compile_err->message << std::endl;
            hs_free_compile_error(compile_err);
        } else {
            std::cerr << "Unknown error" << std::endl;
        }
        std::exit(1);
    }
    
    // Allocate scratch space
    hs_scratch_t *scratch = nullptr;
    if (hs_alloc_scratch(database, &scratch) != HS_SUCCESS) {
        std::cerr << "Error: Failed to allocate scratch space" << std::endl;
        hs_free_database(database);
        std::exit(1);
    }
    
    // Scan the data
    if (hs_scan(database, data.c_str(), data.length(), 0, scratch, on_match, nullptr) != HS_SUCCESS) {
        std::cerr << "Error: Failed to scan data" << std::endl;
        hs_free_scratch(scratch);
        hs_free_database(database);
        std::exit(1);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    double elapsed_ms = duration.count() / 1e6;
    
    std::cout << std::fixed;
    std::cout.precision(6);
    std::cout << elapsed_ms << " - " << match_count << std::endl;
    
    // Clean up
    hs_free_scratch(scratch);
    hs_free_database(database);
}

int main(int argc, char* argv[]) {
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