JAVAC=javac
JAVA=java
CLASS_NAME=Benchmark
SOURCE_FILE=$(CLASS_NAME).java
CLASS_FILE=$(CLASS_NAME).class
OUTPUT_DIR=bin
PACKAGE_DIR=$(OUTPUT_DIR)
EXECUTABLE_SCRIPT=$(OUTPUT_DIR)/benchmark

.PHONY: all test clean

all: $(EXECUTABLE_SCRIPT)

$(EXECUTABLE_SCRIPT): $(SOURCE_FILE) | bin
	$(JAVAC) -d $(OUTPUT_DIR) $(SOURCE_FILE)
	echo '#!/bin/bash' > $(EXECUTABLE_SCRIPT)
	echo 'DIR="$$(cd "$$(dirname "$$0")" && pwd)"' >> $(EXECUTABLE_SCRIPT)
	echo 'java -cp "$$DIR" $(CLASS_NAME) "$$@"' >> $(EXECUTABLE_SCRIPT)
	chmod +x $(EXECUTABLE_SCRIPT)

bin:
	mkdir -p bin

test: $(EXECUTABLE_SCRIPT)
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE_SCRIPT)
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

clean:
	rm -rf $(OUTPUT_DIR)

install-deps:
	@echo "Installing Java dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y openjdk-11-jdk; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y java-11-openjdk-devel; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache openjdk11; \
	else \
		echo "Package manager not found. Please install Java manually."; \
		echo "Visit: https://openjdk.org/install/"; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 