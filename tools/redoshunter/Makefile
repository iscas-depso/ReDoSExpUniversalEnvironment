# ReDoSHunter Tool Makefile

# Variables
SRC_DIR = src
MAIN_CLASS = cn.ac.ios.ReDoSMain
JAR_NAME = ReDoSHunter.jar
TEST_DIR = tests

# Default target
all: build

# Build the Java application
build:
	@echo "Building ReDoSHunter with Java 8..."
	cd $(SRC_DIR) && JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 mvn clean compile assembly:single
	@echo "Copying JAR file..."
	cp $(SRC_DIR)/target/ReDoSHunter-1.0.0.jar ./$(JAR_NAME)
	@echo "Build complete!"

# Clean build artifacts
clean:
	cd $(SRC_DIR) && mvn clean
	rm -f $(JAR_NAME)
	@echo "Clean complete!"

# Run tests
test: build
	@echo "Running ReDoSHunter tests..."
	chmod +x $(TEST_DIR)/simple_test.sh
	./$(TEST_DIR)/simple_test.sh
	@echo "Tests complete!"

# Help target
help:
	@echo "Available targets:"
	@echo "  all     - Build the tool (default)"
	@echo "  build   - Build the ReDoSHunter JAR file"
	@echo "  clean   - Clean build artifacts"
	@echo "  test    - Run tests"
	@echo "  help    - Show this help message"

.PHONY: all build clean test help 