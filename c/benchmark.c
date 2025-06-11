#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <time.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>

#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

char *base64_decode(const char *input, size_t *output_length)
{
    BIO *bio, *b64;
    int decode_length = strlen(input);
    char *buffer = (char *)malloc(decode_length + 1);
    
    if (buffer == NULL) {
        return NULL;
    }
    
    bio = BIO_new_mem_buf(input, -1);
    b64 = BIO_new(BIO_f_base64());
    bio = BIO_push(b64, bio);
    
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    *output_length = BIO_read(bio, buffer, decode_length);
    buffer[*output_length] = '\0';
    
    BIO_free_all(bio);
    
    return buffer;
}

char *read_file(char *filename)
{
  char *data;
  long length = 0;

  FILE *fh = fopen(filename, "rb");
  if (fh == NULL) {
    fprintf(stderr, "Error: Cannot open file %s\n", filename);
    exit(1);
  }

  fseek(fh, 0, SEEK_END);
  length = ftell(fh);
  fseek(fh, 0, SEEK_SET);

  data = malloc(length + 1);
  if (data == NULL) {
    fprintf(stderr, "Error: Memory allocation failed\n");
    exit(1);
  }

  size_t result = fread(data, 1, (size_t)length, fh);
  if (result != (size_t)length) {
    fprintf(stderr, "Error: Failed to read file\n");
    exit(1);
  }
  
  data[length] = '\0';  // Null-terminate the string
  fclose(fh);

  return data;
}

void measure(char *data, char *pattern, int full_match)
{
  int count = 0;
  double elapsed;
  struct timespec start, end;
  pcre2_code *re;
  int errorcode;
  PCRE2_SIZE erroroffset;
  pcre2_match_data *match_data;
  int length;
  PCRE2_SIZE offset = 0;
  PCRE2_SIZE *ovector;

  clock_gettime(CLOCK_MONOTONIC, &start);

  re = pcre2_compile((PCRE2_SPTR) pattern, PCRE2_ZERO_TERMINATED, 0, &errorcode, &erroroffset, NULL);
  if (re == NULL) {
    fprintf(stderr, "Error: Failed to compile regex\n");
    exit(1);
  }

  match_data = pcre2_match_data_create_from_pattern(re, NULL);
  length = (int)strlen(data);

  if (full_match) {
    // Full match: entire text must match the regex
    if (pcre2_match(re, (PCRE2_SPTR8) data, length, 0, PCRE2_ANCHORED, match_data, NULL) >= 0) {
      ovector = pcre2_get_ovector_pointer(match_data);
      // Check if the match covers the entire string
      if (ovector[0] == 0 && ovector[1] == (PCRE2_SIZE)length) {
        count = 1;
      }
    }
  } else {
    // Partial match: find all matches in the text
    while (pcre2_match(re, (PCRE2_SPTR8) data, length, offset, 0, match_data, NULL) >= 0) {
      count++;
      ovector = pcre2_get_ovector_pointer(match_data);
      offset = ovector[1];
      
      // Prevent infinite loop on zero-length matches
      if (ovector[0] == ovector[1]) {
        offset++;
        if (offset >= (PCRE2_SIZE)length) break;
      }
    }
  }

  clock_gettime(CLOCK_MONOTONIC, &end);
  elapsed = ((end.tv_sec - start.tv_sec) * 1e9 + end.tv_nsec - start.tv_nsec) / 1e6;

  printf("%.6f - %d\n", elapsed, count);

  pcre2_match_data_free(match_data);
  pcre2_code_free(re);
}

int main(int argc, char **argv)
{
  if (argc != 4) {
    printf("Usage: %s <base64_regex> <filename> <match_mode>\n", argv[0]);
    printf("  base64_regex: Base64-encoded regular expression\n");
    printf("  filename: Path to the file containing text to match\n");
    printf("  match_mode: 1 for full match, 0 for partial match\n");
    exit(1);
  }

  // Decode the base64 regex
  size_t decoded_length;
  char *regex = base64_decode(argv[1], &decoded_length);
  if (regex == NULL) {
    fprintf(stderr, "Error: Failed to decode base64 regex\n");
    exit(1);
  }

  // Read file content
  char *data = read_file(argv[2]);

  // Parse match mode
  int match_mode = atoi(argv[3]);
  if (match_mode != 0 && match_mode != 1) {
    fprintf(stderr, "Error: match_mode must be 0 or 1\n");
    exit(1);
  }

  // Measure and output results
  measure(data, regex, match_mode);

  // Clean up
  free(data);
  free(regex);

  return 0;
}
