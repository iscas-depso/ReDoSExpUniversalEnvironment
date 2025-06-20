#!/bin/bash

# Script to run all tests inside the Docker container
# This script should be run from inside the engines directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Multi-Language Regex Benchmark Test Suite${NC}"
echo -e "${CYAN}  (Running inside Docker container)${NC}"
echo -e "${CYAN}============================================${NC}"
echo

# Check if we're in the right directory (should be in engines folder)
if [ ! -d "awk" ] || [ ! -d "c" ] || [ ! -d "cpp" ]; then
    echo -e "${RED}ERROR: Engine directories not found!${NC}"
    echo "Please run this script from /app/engines directory"
    exit 1
fi

# List of all engines
ENGINES=(
    "awk"
    "c"
    "cpp"  
    "csharp"
    "csharp_nonbacktracking"
    "go"
    "grep"
    "hyperscan"
    "java8"
    "java11"
    "nodejs14"
    "nodejs21"
    "perl"
    "php"
    "python"
    "re2"
    "ruby"
    "rust"
    "srm"
)

# Test results tracking
TOTAL_ENGINES=${#ENGINES[@]}
PASSED_ENGINES=0
FAILED_ENGINES=()
START_TIME=$(date +%s)

echo -e "${BLUE}Found $TOTAL_ENGINES engines to test${NC}"
echo

# Function to run tests for a single engine
run_engine_tests() {
    local engine="$1"
    local engine_num="$2"
    
    echo -e "${YELLOW}[$engine_num/$TOTAL_ENGINES] Testing $engine engine...${NC}"
    echo -e "${CYAN}===========================================${NC}"
    
    # Check if engine directory exists
    if [ ! -d "$engine" ]; then
        echo -e "${RED}✗ Engine directory $engine not found${NC}"
        return 1
    fi
    
    # Change to engine directory
    cd "$engine" || {
        echo -e "${RED}✗ Failed to change to $engine directory${NC}"
        return 1
    }
    
    # Special handling for Node.js 21 which needs NVM
    if [ "$engine" = "nodejs21" ]; then
        if source /home/developer/.nvm/nvm.sh && nvm use 21.7.3 && make test; then
            echo -e "${GREEN}✓ $engine tests PASSED${NC}"
            cd ..
            return 0
        else
            echo -e "${RED}✗ $engine tests FAILED${NC}"
            cd ..
            return 1
        fi
    else
        # Regular test execution
        if make test; then
            echo -e "${GREEN}✓ $engine tests PASSED${NC}"
            cd ..
            return 0
        else
            echo -e "${RED}✗ $engine tests FAILED${NC}"
            cd ..
            return 1
        fi
    fi
}

# Function to test a single engine (for command line usage)
test_single_engine() {
    local engine="$1"
    
    # Check if engine exists
    local found=0
    for e in "${ENGINES[@]}"; do
        if [[ "$e" == "$engine" ]]; then
            found=1
            break
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo -e "${RED}ERROR: Unknown engine '$engine'${NC}"
        echo -e "${BLUE}Available engines: ${ENGINES[*]}${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Testing single engine: $engine${NC}"
    echo
    
    if run_engine_tests "$engine" "1"; then
        echo
        echo -e "${GREEN}✓ $engine test completed successfully!${NC}"
        return 0
    else
        echo
        echo -e "${RED}✗ $engine test failed!${NC}"
        return 1
    fi
}

# Check command line arguments
if [ $# -eq 1 ]; then
    # Single engine test
    test_single_engine "$1"
    exit $?
elif [ $# -gt 1 ]; then
    # Multiple specific engines
    echo -e "${BLUE}Testing specific engines: $*${NC}"
    echo
    
    passed=0
    failed=0
    failed_engines=()
    
    for engine in "$@"; do
        if test_single_engine "$engine"; then
            ((passed++))
        else
            ((failed++))
            failed_engines+=("$engine")
        fi
        echo
    done
    
    # Summary for multiple engines
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}              TEST SUMMARY${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo
    echo -e "${BLUE}Total engines tested: $(($# ))${NC}"
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"
    
    if [ ${#failed_engines[@]} -gt 0 ]; then
        echo
        echo -e "${RED}Failed engines: ${failed_engines[*]}${NC}"
    fi
    
    if [ $failed -eq 0 ]; then
        echo
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo
        echo -e "${RED}❌ Some tests failed!${NC}"
        exit 1
    fi
fi

# Run tests for all engines (default behavior)
for i in "${!ENGINES[@]}"; do
    engine="${ENGINES[$i]}"
    engine_num=$((i + 1))
    
    echo
    if run_engine_tests "$engine" "$engine_num"; then
        ((PASSED_ENGINES++))
    else
        FAILED_ENGINES+=("$engine")
    fi
    echo
done

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# Print summary
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}              TEST SUMMARY${NC}"
echo -e "${CYAN}============================================${NC}"
echo
echo -e "${BLUE}Total engines tested: $TOTAL_ENGINES${NC}"
echo -e "${GREEN}Passed: $PASSED_ENGINES${NC}"
echo -e "${RED}Failed: $((TOTAL_ENGINES - PASSED_ENGINES))${NC}"

if [ ${#FAILED_ENGINES[@]} -gt 0 ]; then
    echo
    echo -e "${RED}Failed engines:${NC}"
    for engine in "${FAILED_ENGINES[@]}"; do
        echo -e "${RED}  - $engine${NC}"
    done
fi

echo
echo -e "${BLUE}Total time: ${MINUTES}m ${SECONDS}s${NC}"
echo

# Exit with appropriate code
if [ $PASSED_ENGINES -eq $TOTAL_ENGINES ]; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above for details.${NC}"
    exit 1
fi 