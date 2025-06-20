DOTNET=dotnet
PROJECT=benchmark.csproj
TARGET=bin/Release/net7.0/benchmark
OUTPUT_DIR=bin
EXECUTABLE=$(OUTPUT_DIR)/benchmark

.PHONY: all test clean restore

all: $(EXECUTABLE)

$(EXECUTABLE): $(PROJECT) Benchmark.cs | bin
	$(DOTNET) publish -c Release -o $(OUTPUT_DIR) --self-contained false
	# Make the executable file executable if it exists
	chmod +x $(OUTPUT_DIR)/benchmark 2>/dev/null || true

bin:
	mkdir -p bin

restore:
	$(DOTNET) restore

test: $(EXECUTABLE)
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE)
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

clean:
	$(DOTNET) clean
	rm -rf bin obj
	mkdir -p bin

install-deps:
	@echo "Installing .NET 7.0 dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y dotnet-sdk-7.0; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y dotnet-sdk-7.0; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache dotnet7-sdk; \
	else \
		echo "Package manager not found. Please install .NET 7.0 SDK manually."; \
		echo "Visit: https://dotnet.microsoft.com/download/dotnet/7.0"; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  restore     - Restore NuGet packages"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 