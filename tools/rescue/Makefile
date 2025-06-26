JAVA_VERSION := 17
MAVEN_CMD := mvn
TARGET_JAR := target/ReScue-0.0.1-SNAPSHOT.jar
DEPENDENCY_DIR := target/dependency-jars

.PHONY: all build clean test install-deps

# Default target
all: build

# Build the project
build:
	@echo "Building ReScue tool..."
	@echo "Using Java version: $(JAVA_VERSION)"
	JAVA_HOME=/usr/lib/jvm/java-$(JAVA_VERSION)-openjdk-amd64 $(MAVEN_CMD) clean package -q
	@if [ -f "$(TARGET_JAR)" ]; then \
		echo "Build completed successfully. JAR created: $(TARGET_JAR)"; \
	else \
		echo "Build failed. JAR not found at $(TARGET_JAR)"; \
		echo "Available files in target directory:"; \
		ls -la target/ || echo "Target directory not found"; \
		exit 1; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	$(MAVEN_CMD) clean
	@echo "Clean completed."

# Install dependencies (if needed)
install-deps:
	@echo "Installing Maven dependencies..."
	$(MAVEN_CMD) dependency:resolve

# Run tests
test:
	@echo "Running ReScue tool tests..."
	@if [ ! -f "$(TARGET_JAR)" ]; then \
		echo "JAR file not found. Building first..."; \
		$(MAKE) build; \
	fi
	@echo "Testing with Java version..."
	java -version
	cd tests && bash simple_test.sh

# Show help
help:
	@echo "Available targets:"
	@echo "  all        - Build the project (default)"
	@echo "  build      - Build the project with Maven"
	@echo "  clean      - Clean build artifacts"
	@echo "  test       - Run tests"
	@echo "  install-deps - Install Maven dependencies"
	@echo "  help       - Show this help message" 