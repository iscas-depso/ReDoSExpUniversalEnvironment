CARGO=cargo
TARGET=bin/benchmark
BINARY_NAME=benchmark

.PHONY: all test clean install-deps help

all: $(TARGET)

$(TARGET): src/main.rs Cargo.toml | bin
	$(CARGO) build --release
	cp target/release/$(BINARY_NAME) $(TARGET)

bin:
	mkdir -p bin

test: $(TARGET)
	chmod +x tests/run_tests.sh
	cd tests && ./run_tests.sh

simple-test: $(TARGET)
	chmod +x tests/simple_test.sh
	cd tests && ./simple_test.sh

clean:
	$(CARGO) clean
	rm -f $(TARGET)
	rmdir bin 2>/dev/null || true

install-deps:
	@echo "Installing Rust dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source ~/.cargo/env; \
	elif command -v yum >/dev/null 2>&1; then \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source ~/.cargo/env; \
	elif command -v dnf >/dev/null 2>&1; then \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source ~/.cargo/env; \
	elif command -v apk >/dev/null 2>&1; then \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source ~/.cargo/env; \
	else \
		echo "Package manager not found. Please install Rust manually."; \
		echo "Visit https://rustup.rs/ for installation instructions."; \
	fi
	@echo "Dependencies: regex, base64 (managed by Cargo)"

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple test"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required Rust dependencies"
	@echo "  help        - Show this help message" 