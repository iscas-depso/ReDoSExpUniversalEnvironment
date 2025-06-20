RUBY=ruby
TARGET=bin/benchmark
SOURCE=benchmark.rb

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
	@echo "Installing Ruby dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y ruby; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y ruby; \
	elif command -v dnf >/dev/null 2>&1; then \
		dnf install -y ruby; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache ruby; \
	else \
		echo "Package manager not found. Please install Ruby manually."; \
		echo "Ruby comes with base64 library built-in."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Prepare the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple test"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required Ruby dependencies"
	@echo "  help        - Show this help message" 