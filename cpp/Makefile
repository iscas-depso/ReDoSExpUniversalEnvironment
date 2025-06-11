CXX=g++
CXXFLAGS=-std=c++11 -Wall -Wextra
LIBS=-lboost_regex -lssl -lcrypto
TARGET=bin/benchmark
SOURCE=benchmark.cpp

.PHONY: all test clean

all: $(TARGET)

$(TARGET): $(SOURCE) | bin
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE) $(LIBS) -DREGEX_NAMESPACE=boost

bin:
	mkdir -p bin

test: $(TARGET)
	chmod +x tests/run_tests.sh
	cd tests && ./run_tests.sh

simple-test: $(TARGET)
	chmod +x tests/simple_test.sh
	cd tests && ./simple_test.sh

clean:
	rm -f $(TARGET)
	rmdir bin 2>/dev/null || true

install-deps:
	@echo "Installing dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y libssl-dev libboost-regex-dev build-essential; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y openssl-devel boost-devel gcc-c++; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache openssl-dev boost-dev build-base; \
	else \
		echo "Package manager not found. Please install libssl-dev and libboost-regex-dev manually."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 