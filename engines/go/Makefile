GO=go
BINARY_NAME=benchmark
OUTPUT_DIR=bin
EXECUTABLE=$(OUTPUT_DIR)/$(BINARY_NAME)

.PHONY: all test clean mod-tidy

all: $(EXECUTABLE)

$(EXECUTABLE): benchmark.go go.mod | bin
	$(GO) build -o $(EXECUTABLE) .

bin:
	mkdir -p bin

mod-tidy:
	$(GO) mod tidy

test: $(EXECUTABLE)
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE)
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

clean:
	$(GO) clean
	rm -rf $(OUTPUT_DIR)

install-deps:
	@echo "Installing Go dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y golang-go; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y golang; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache go; \
	else \
		echo "Package manager not found. Please install Go manually."; \
		echo "Visit: https://golang.org/doc/install"; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  mod-tidy    - Tidy go modules"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 