# Makefile for SRM C# Benchmark Program

.PHONY: all build test simple-test clean install-deps help

# Default target
all: build bin

# Build the project
build:
	@echo "Building SRM C# benchmark program..."
	dotnet restore
	dotnet build
	@echo "Build completed successfully"

# Create bin directory and executable script
bin: build
	@mkdir -p bin
	@echo '#!/bin/bash' > bin/benchmark
	@echo 'cd "$$(dirname "$$0")/.."' >> bin/benchmark
	@echo 'exec dotnet run -- "$$@"' >> bin/benchmark
	@chmod +x bin/benchmark
	@echo "Created bin/benchmark executable script"

# Run comprehensive tests
test: build
	@echo "Running comprehensive tests..."
	@cd tests && chmod +x run_tests.sh && ./run_tests.sh

# Run simple tests
simple-test: build
	@echo "Running simple tests..."
	@cd tests && chmod +x simple_test.sh && ./simple_test.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	dotnet clean
	rm -rf bin obj

# Install dependencies (restore packages)
install-deps:
	@echo "Installing dependencies..."
	dotnet restore
	@echo "Dependencies installed successfully"

# Show help
help:
	@echo "Available targets:"
	@echo "  all         - Build the program (default)"
	@echo "  build       - Build the program"
	@echo "  bin         - Create bin directory with executable"
	@echo "  test        - Run comprehensive tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Clean build artifacts"
	@echo "  install-deps- Install dependencies"
	@echo "  help        - Show this help message" 