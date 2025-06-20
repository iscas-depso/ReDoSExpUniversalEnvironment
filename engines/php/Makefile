PHP=php
TARGET=bin/benchmark
SOURCE=benchmark.php

.PHONY: all test clean install-deps help

all: $(TARGET)

$(TARGET): $(SOURCE) | bin
	cp $(SOURCE) $(TARGET)
	chmod +x $(TARGET)

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
	@echo "Installing PHP dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y php-cli; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y php-cli; \
	elif command -v dnf >/dev/null 2>&1; then \
		dnf install -y php-cli; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache php-cli; \
	else \
		echo "Package manager not found. Please install PHP CLI manually."; \
		echo "PHP comes with base64 functions built-in."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Prepare the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple test"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required PHP dependencies"
	@echo "  help        - Show this help message" 