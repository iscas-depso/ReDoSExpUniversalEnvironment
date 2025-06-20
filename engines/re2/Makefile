# RE2 Benchmark Makefile

CXX = g++
CXXFLAGS = -std=c++11 -O3 -Wall -Wextra
LDFLAGS = -lre2

# Project structure
SRC_DIR = src
BIN_DIR = bin
TEST_DIR = tests

# Target binary
TARGET = $(BIN_DIR)/benchmark
SOURCE = $(SRC_DIR)/benchmark.cpp

.PHONY: all clean test

all: $(TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(TARGET): $(SOURCE) | $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -rf $(BIN_DIR)

test: $(TARGET)
	cd $(TEST_DIR) && ./run_tests.sh

.PHONY: install-deps
install-deps:
	@echo "Installing dependencies..."
	@echo "Please install libre2-dev package"
	@echo "Ubuntu/Debian: sudo apt-get install libre2-dev"
	@echo "RedHat/CentOS: sudo yum install re2-devel"
