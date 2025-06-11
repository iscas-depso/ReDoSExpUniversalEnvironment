# Java 8 specific configuration
JAVA_VERSION=8
JAVA_HOME_8=/usr/lib/jvm/java-8-openjdk-amd64
JAVAC=$(JAVA_HOME_8)/bin/javac
JAVA=$(JAVA_HOME_8)/bin/java

CLASS_NAME=Benchmark
SOURCE_FILE=$(CLASS_NAME).java
CLASS_FILE=$(CLASS_NAME).class
OUTPUT_DIR=bin
PACKAGE_DIR=$(OUTPUT_DIR)
EXECUTABLE_SCRIPT=$(OUTPUT_DIR)/benchmark

.PHONY: all test clean java-version

all: java-version $(EXECUTABLE_SCRIPT)

java-version:
	@echo "Using Java 8 from: $(JAVA_HOME_8)"
	@if [ -f "$(JAVA_HOME_8)/bin/java" ]; then \
		$(JAVA_HOME_8)/bin/java -version; \
	else \
		echo "Error: Java 8 not found at $(JAVA_HOME_8)"; \
		exit 1; \
	fi

$(EXECUTABLE_SCRIPT): $(SOURCE_FILE) | bin
	$(JAVAC) -d $(OUTPUT_DIR) -source $(JAVA_VERSION) -target $(JAVA_VERSION) $(SOURCE_FILE)
	echo '#!/bin/bash' > $(EXECUTABLE_SCRIPT)
	echo '# Java 8 Benchmark Wrapper' >> $(EXECUTABLE_SCRIPT)
	echo 'JAVA_HOME_8=/usr/lib/jvm/java-8-openjdk-amd64' >> $(EXECUTABLE_SCRIPT)
	echo 'DIR="$$(cd "$$(dirname "$$0")" && pwd)"' >> $(EXECUTABLE_SCRIPT)
	echo '"$$JAVA_HOME_8/bin/java" -cp "$$DIR" $(CLASS_NAME) "$$@"' >> $(EXECUTABLE_SCRIPT)
	chmod +x $(EXECUTABLE_SCRIPT)

bin:
	mkdir -p bin

test: $(EXECUTABLE_SCRIPT)
	@echo "Running Java 8 tests..."
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE_SCRIPT)
	@echo "Running Java 8 simple test..."
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

clean:
	rm -rf $(OUTPUT_DIR)

install-deps:
	@echo "Installing Java 8 dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y openjdk-8-jdk; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y java-1.8.0-openjdk-devel; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache openjdk8; \
	else \
		echo "Package manager not found. Please install Java 8 manually."; \
		echo "Visit: https://openjdk.org/install/"; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the Java 8 benchmark program"
	@echo "  java-version- Show Java 8 version information"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 