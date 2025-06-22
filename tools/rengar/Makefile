JAVA_VERSION := 17
MAVEN_CMD := mvn
SOURCE_DIR := src
TARGET_JAR := Rengar.jar
ORIGINAL_JAR := $(SOURCE_DIR)/target/Rengar-1.0-jar-with-dependencies.jar

.PHONY: all build clean test

# Default target
all: build

# Build the project
build:
	@echo "Building Rengar tool..."
	@echo "Using Java version: $(JAVA_VERSION)"
	cd $(SOURCE_DIR) && JAVA_HOME=/usr/lib/jvm/java-$(JAVA_VERSION)-openjdk-amd64 $(MAVEN_CMD) clean compile assembly:single -DskipTests
	@if [ -f "$(ORIGINAL_JAR)" ]; then \
		cp "$(ORIGINAL_JAR)" "$(TARGET_JAR)"; \
		echo "Build completed successfully. JAR created: $(TARGET_JAR)"; \
	else \
		echo "Build failed. JAR not found at $(ORIGINAL_JAR)"; \
		echo "Available files in target directory:"; \
		ls -la $(SOURCE_DIR)/target/ || echo "Target directory not found"; \
		exit 1; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	cd $(SOURCE_DIR) && $(MAVEN_CMD) clean
	rm -f $(TARGET_JAR)
	@echo "Clean completed."

# Run tests
test:
	@echo "Running Rengar tool tests..."
	@if [ ! -f "$(TARGET_JAR)" ]; then \
		echo "JAR file not found. Building first..."; \
		$(MAKE) build; \
	fi
	@echo "Testing with Docker Java version..."
	java -version
	cd tests && bash simple_test.sh

# Install dependencies (if needed)
install-deps:
	@echo "Installing Maven dependencies..."
	cd $(SOURCE_DIR) && $(MAVEN_CMD) dependency:resolve

# Show help
help:
	@echo "Available targets:"
	@echo "  all        - Build the project (default)"
	@echo "  build      - Build the project and create JAR"
	@echo "  clean      - Clean build artifacts"
	@echo "  test       - Run tests"
	@echo "  install-deps - Install Maven dependencies"
	@echo "  help       - Show this help message" 