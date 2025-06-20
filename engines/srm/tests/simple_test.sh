#!/bin/bash

# Simple test script for SRM C# benchmark program

echo "=== Running SRM C# Simple Tests ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if dotnet is available
if ! command -v dotnet &> /dev/null; then
    echo -e "${RED}FAILED: dotnet not found${NC}"
    echo "Please install .NET Core SDK."
    exit 1
fi

# Build the project
echo "Building project..."
cd ..
dotnet restore > /dev/null 2>&1
dotnet build > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}FAILED: Project build failed${NC}"
    exit 1
fi
cd tests
echo -e "${GREEN}Project built successfully${NC}"
echo

# Test 1: Simple word matching
echo -e "${YELLOW}Test 1: Simple word match${NC}"
echo "  Regex: cat (Y2F0)"
echo "  File: simple_test.txt"
echo "  Mode: 0 (partial match)"

result=$(dotnet run --project .. -- "Y2F0" "simple_test.txt" "0" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "  Result: $result"
    echo -e "  ${GREEN}PASSED${NC}"
else
    echo -e "  ${RED}FAILED: Exit code $exit_code${NC}"
    echo "  Output: $result"
fi
echo

# Test 2: Full match test
echo -e "${YELLOW}Test 2: Full match test${NC}"
echo "  Regex: hello world (aGVsbG8gd29ybGQ=)"
echo "  File: full_match_test.txt"
echo "  Mode: 1 (full match)"

result=$(dotnet run --project .. -- "aGVsbG8gd29ybGQ=" "full_match_test.txt" "1" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "  Result: $result"
    echo -e "  ${GREEN}PASSED${NC}"
else
    echo -e "  ${RED}FAILED: Exit code $exit_code${NC}"
    echo "  Output: $result"
fi
echo

echo "=== Simple tests completed ===" 