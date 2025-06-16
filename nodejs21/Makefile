# Node.js 21 specific configuration with V8 Non-Backtracking RegExp Engine
NODE_VERSION=21.7.3
NVM_DIR=$(HOME)/.nvm
SHELL := /bin/bash

PROGRAM_FILE=benchmark.js
OUTPUT_DIR=bin
EXECUTABLE_SCRIPT=$(OUTPUT_DIR)/benchmark

# V8 Non-Backtracking RegExp Engine flags
NODE_FLAGS=--enable-experimental-regexp-engine --default-to-experimental-regexp-engine

.PHONY: all test clean node-version install-nvm setup-node

all: node-version $(EXECUTABLE_SCRIPT)

node-version:
	@echo "Checking Node.js environment..."
	@if [ -f "$(NVM_DIR)/nvm.sh" ]; then \
		echo "Using nvm from: $(NVM_DIR)"; \
		bash -c "source $(NVM_DIR)/nvm.sh && nvm use $(NODE_VERSION) && node --version && npm --version"; \
	else \
		echo "Using system Node.js"; \
		node --version; \
		npm --version; \
	fi

$(EXECUTABLE_SCRIPT): $(PROGRAM_FILE) | bin
	@echo "Creating Node.js 21 executable wrapper with V8 non-backtracking RegExp engine..."
	echo '#!/bin/bash' > $(EXECUTABLE_SCRIPT)
	echo '# Node.js 21 Benchmark Wrapper with V8 Non-Backtracking RegExp Engine' >> $(EXECUTABLE_SCRIPT)
	echo 'export NVM_DIR="$(HOME)/.nvm"' >> $(EXECUTABLE_SCRIPT)
	echo 'DIR="$$(cd "$$(dirname "$$0")" && pwd)"' >> $(EXECUTABLE_SCRIPT)
	echo 'SCRIPT_DIR="$$(dirname "$$DIR")"' >> $(EXECUTABLE_SCRIPT)
	echo 'NODE_FLAGS="$(NODE_FLAGS)"' >> $(EXECUTABLE_SCRIPT)
	echo 'if [ -f "$$NVM_DIR/nvm.sh" ]; then' >> $(EXECUTABLE_SCRIPT)
	echo '    source "$$NVM_DIR/nvm.sh"' >> $(EXECUTABLE_SCRIPT)
	echo '    nvm use $(NODE_VERSION) >/dev/null 2>&1' >> $(EXECUTABLE_SCRIPT)
	echo '    node $$NODE_FLAGS "$$SCRIPT_DIR/$(PROGRAM_FILE)" "$$@"' >> $(EXECUTABLE_SCRIPT)
	echo 'else' >> $(EXECUTABLE_SCRIPT)
	echo '    node $$NODE_FLAGS "$$SCRIPT_DIR/$(PROGRAM_FILE)" "$$@"' >> $(EXECUTABLE_SCRIPT)
	echo 'fi' >> $(EXECUTABLE_SCRIPT)
	chmod +x $(EXECUTABLE_SCRIPT)

bin:
	mkdir -p bin

test: $(EXECUTABLE_SCRIPT)
	@echo "Running Node.js 21 tests..."
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE_SCRIPT)
	@echo "Running Node.js 21 simple test..."
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

v8-test: $(EXECUTABLE_SCRIPT)
	@echo "Running Node.js 21 V8 Non-Backtracking RegExp Engine tests..."
	chmod +x tests/v8_engine_test.sh 2>/dev/null || true
	cd tests && ./v8_engine_test.sh

all-tests: test v8-test
	@echo "All Node.js 21 tests completed successfully!"

clean:
	rm -rf $(OUTPUT_DIR)

install-nvm:
	@echo "Installing nvm (Node Version Manager)..."
	@if [ ! -d "$(NVM_DIR)" ]; then \
		curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash; \
		echo "Please restart your shell or run: source ~/.bashrc"; \
	else \
		echo "nvm already installed at $(NVM_DIR)"; \
	fi

setup-node: install-nvm
	@echo "Setting up Node.js $(NODE_VERSION)..."
	bash -c "source $(NVM_DIR)/nvm.sh && nvm install $(NODE_VERSION) && nvm use $(NODE_VERSION)"

install-deps: setup-node
	@echo "Installing Node.js 21 dependencies..."
	bash -c "source $(NVM_DIR)/nvm.sh && nvm use $(NODE_VERSION) && npm install"

help:
	@echo "Available targets:"
	@echo "  all         - Build the Node.js 21 benchmark program"
	@echo "  node-version- Show Node.js 21 version information"
	@echo "  test        - Run all benchmark tests"
	@echo "  simple-test - Run simple tests"
	@echo "  v8-test     - Run V8 Non-Backtracking RegExp Engine tests"
	@echo "  all-tests   - Run both benchmark and V8 engine tests"
	@echo "  clean       - Remove built files"
	@echo "  install-nvm - Install Node Version Manager"
	@echo "  setup-node  - Install and setup Node.js 21"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 