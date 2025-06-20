PYTHON=python3
TARGET=bin/benchmark
SOURCE=benchmark.py

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
	@echo "Installing Python dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y python3 python3-pip; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y python3 python3-pip; \
	elif command -v dnf >/dev/null 2>&1; then \
		dnf install -y python3 python3-pip; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache python3 py3-pip; \
	else \
		echo "Package manager not found. Please install Python 3 manually."; \
		echo "Python 3 comes with base64 and re modules built-in."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Prepare the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple test"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required Python dependencies"
	@echo "  help        - Show this help message" 