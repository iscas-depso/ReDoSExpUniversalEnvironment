CC=gcc
CFLAGS=-Wall -Wextra -std=c99
LIBS=-lpcre2-8 -lssl -lcrypto
TARGET=bin/benchmark
SOURCE=benchmark.c

.PHONY: all test clean

all: $(TARGET)

$(TARGET): $(SOURCE) | bin
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE) $(LIBS)

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
		apt-get update && apt-get install -y libssl-dev libpcre2-dev build-essential; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y openssl-devel pcre2-devel gcc; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache openssl-dev pcre2-dev build-base; \
	else \
		echo "Package manager not found. Please install libssl-dev and libpcre2-dev manually."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 