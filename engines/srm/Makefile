# Makefile for SRM C# Benchmark Program

DOTNET=dotnet
PROJECT=benchmark.csproj
OUTPUT_DIR=bin
EXECUTABLE=$(OUTPUT_DIR)/benchmark

.PHONY: all build test simple-test clean install-deps help

# Default target
all: $(EXECUTABLE)

# Build and publish the project
$(EXECUTABLE): $(PROJECT) Benchmark.cs | bin
	$(DOTNET) publish -c Release -o $(OUTPUT_DIR) --self-contained false
	# Make the executable file executable if it exists
	chmod +x $(OUTPUT_DIR)/benchmark 2>/dev/null || true

# Create bin directory
bin:
	mkdir -p bin

# Run comprehensive tests
test: $(EXECUTABLE)
	@echo "Running comprehensive tests..."
	@cd tests && chmod +x run_tests.sh && ./run_tests.sh

# Run simple tests
simple-test: $(EXECUTABLE)
	@echo "Running simple tests..."
	@cd tests && chmod +x simple_test.sh && ./simple_test.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	$(DOTNET) clean
	rm -rf bin obj

# Install dependencies (restore packages)
install-deps:
	@echo "Installing dependencies..."
	$(DOTNET) restore
	@echo "Dependencies installed successfully"

# Show help
help:
	@echo "Available targets:"
	@echo "  all         - Build the program (default)"
	@echo "  test        - Run comprehensive tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Clean build artifacts"
	@echo "  install-deps- Install dependencies"
	@echo "  help        - Show this help message" 