#include <iostream>
#include <fstream>
#include <locale>
#include <codecvt>
#include <unistd.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>
#include <chrono>
#include <nlohmann/json.hpp>
#include "Solver/solver_kind.h"
#include "Parser/parser.h"
#include "Solver/DetectAmbiguity_WithLookAround/DetectAmbiguity.h"

using json = nlohmann::json;

// Base64 decode function
std::string base64_decode(const std::string& encoded_string) {
    BIO *bio, *b64;
    int decodeLen = encoded_string.length();
    char *buffer = new char[decodeLen];
    
    bio = BIO_new_mem_buf(encoded_string.c_str(), -1);
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_push(b64, bio);
    
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    int length = BIO_read(bio, buffer, decodeLen);
    BIO_free_all(bio);
    
    std::string result(buffer, length);
    delete[] buffer;
    return result;
}

// Base64 encode function
std::string base64_encode(const std::string& input) {
    BIO *bio, *b64;
    BUF_MEM *bufferPtr;
    
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new(BIO_s_mem());
    bio = BIO_push(b64, bio);
    
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    BIO_write(bio, input.c_str(), input.length());
    BIO_flush(bio);
    BIO_get_mem_ptr(bio, &bufferPtr);
    
    std::string result(bufferPtr->data, bufferPtr->length);
    BIO_free_all(bio);
    return result;
}

int main(int argc, char* argv[]){

  if (argc != 9){
    std::cout << "parameter error" << std::endl;
    std::cout << "Usage: ./GREWIA [Base64Regex] [OutputJsonFile] [OutputDirectory] [AttackStringLength] [SimplifiedModeOn] [DecrementalOn] [MatchingFunction] [Regex Engine]\n" << std::endl;
    std::cout << "[Base64Regex]: Base64 encoded regex pattern.\n" << std::endl;
    std::cout << "[OutputJsonFile]: Path of the output JSON file.\n" << std::endl;
    std::cout << "[OutputDirectory]: Path of a directory where the candidate attack string will be write to.\n" << std::endl;
    std::cout << "[AttackStringLength]: Length of candidate attack string.\n" << std::endl;
    std::cout << "[SimplifiedModeOn]: Set to 1 indicate letting GREWIA generate a attack strings; Set to 0 indicate letting GREWIA generate a series of attack strings.\n" << std::endl;
    std::cout << "[DecrementalOn]: Set to 1 indicate Decremental method is on and vice verse.\n" << std::endl;
    std::cout << "[MatchingFunction]: Set to 1 indicate targeting to partialmatch; Set to 0 indicate targeting to fullmatch.\n" << std::endl;
    std::cout << "[Regex Engine]: Set to a specific regex engine which are Java, JavaScript, Perl, PHP, Python, Boost, C#. And the candidate attack string will be verified in those engines. \n" << std::endl;
    return 0;
  }

  // Start timing
  auto start_time = std::chrono::high_resolution_clock::now();
  
  // Decode base64 regex
  std::string base64_regex = argv[1];
  std::string decoded_regex = base64_decode(base64_regex);
  
  std::vector<std::wstring> Regex_list;
  std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;
  std::wstring unicodeStr = converter.from_bytes(decoded_regex);
  
  // Remove carriage return if present
  wchar_t c = unicodeStr.back();
  if (c == '\r'){
    unicodeStr.pop_back();
  }
  
  // Handle regex delimiters
  if (unicodeStr[0] == '/'){
    for (int j = unicodeStr.length()-1; j > 1; j--){
      if (unicodeStr[j] == '/' ){
        unicodeStr.erase(j, unicodeStr.length());
        unicodeStr.erase(0, 1);
        break;
      }
    }
  }
  
  // Handle partial matching
  if (std::stoi(argv[7]) == 1){
    int i = 0;
    while (unicodeStr[i] == '(')
      i++;
    if (unicodeStr[i] != '^'){
      unicodeStr.insert(0, L".*(");
      unicodeStr.insert(unicodeStr.size(), L")");
    }
  }
  
  Regex_list.emplace_back(unicodeStr);
  
  // Initialize result variables
  bool is_redos = false;
  std::string prefix = "";
  std::string infix = "";
  std::string suffix = "";
  int repeat_times = -1;
  
  std::vector<solverbin::REnodeClass> ReList;
  std::wcout.sync_with_stdio(true);
  
  for (auto str : Regex_list){
    if (solverbin::debug.PrintRegexString) std::wcout << L"Regex: " << str << std::endl;
    auto ren = solverbin::Parer(str, true);
    ReList.emplace_back(ren.Re);
    auto kk = solverbin::DetectABTNFA_Lookaround(ren.Re, std::stoi(argv[4]), argv[3], std::stoi(argv[5]), std::stoi(argv[6]), std::stoi(argv[7]), 0);
    kk.RegexFile = "base64_input";
    kk.Regex = decoded_regex;
    kk.MatchingFunction = argv[7];
    kk.RegexEngine = argv[8];
    auto k1 = kk.IsABT(kk.SSBegin);
    if (k1){
      is_redos = true;
      prefix = kk.InterStr;
      infix = kk.WitnessStr;
      suffix = kk.Suffix;  // GREWIA doesn't seem to provide suffix in the original code
      std::cout <<  "prefix: " << kk.InterStr << std::endl;
      std::cout << "infix: " << kk.WitnessStr << std::endl;
    }
    else {
      std::cout << "false" << std::endl;
    }
  }
  
  // Calculate elapsed time
  auto end_time = std::chrono::high_resolution_clock::now();
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
  
  // Create JSON output using nlohmann/json
  json result;
  result["elapsed_ms"] = std::to_string(duration.count());
  result["is_redos"] = is_redos;
  
  if (is_redos) {
    result["prefix"] = base64_encode(prefix);
    result["infix"] = base64_encode(infix);
    result["suffix"] = base64_encode(suffix);
    result["repeat_times"] = repeat_times;
  } else {
    result["prefix"] = "";
    result["infix"] = "";
    result["suffix"] = "";
    result["repeat_times"] = -1;
  }
  
  // Write JSON to output file
  std::ofstream outfile(argv[2]);
  outfile << result.dump(2);  // Pretty print with 2-space indentation
  outfile.close();
  
  return 0;
} 