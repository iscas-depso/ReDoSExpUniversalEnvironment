# Node.js 14 specific configuration
NODE_VERSION=14.21.3
NVM_DIR=$(HOME)/.nvm
SHELL := /bin/bash

PROGRAM_FILE=benchmark.js
OUTPUT_DIR=bin
EXECUTABLE_SCRIPT=$(OUTPUT_DIR)/benchmark

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
	@echo "Creating Node.js 14 executable wrapper..."
	echo '#!/bin/bash' > $(EXECUTABLE_SCRIPT)
	echo '# Node.js 14 Benchmark Wrapper' >> $(EXECUTABLE_SCRIPT)
	echo 'export NVM_DIR="$(HOME)/.nvm"' >> $(EXECUTABLE_SCRIPT)
	echo 'DIR="$$(cd "$$(dirname "$$0")" && pwd)"' >> $(EXECUTABLE_SCRIPT)
	echo 'SCRIPT_DIR="$$(dirname "$$DIR")"' >> $(EXECUTABLE_SCRIPT)
	echo 'if [ -f "$$NVM_DIR/nvm.sh" ]; then' >> $(EXECUTABLE_SCRIPT)
	echo '    source "$$NVM_DIR/nvm.sh"' >> $(EXECUTABLE_SCRIPT)
	echo '    nvm use $(NODE_VERSION) >/dev/null 2>&1' >> $(EXECUTABLE_SCRIPT)
	echo '    node "$$SCRIPT_DIR/$(PROGRAM_FILE)" "$$@"' >> $(EXECUTABLE_SCRIPT)
	echo 'else' >> $(EXECUTABLE_SCRIPT)
	echo '    node "$$SCRIPT_DIR/$(PROGRAM_FILE)" "$$@"' >> $(EXECUTABLE_SCRIPT)
	echo 'fi' >> $(EXECUTABLE_SCRIPT)
	chmod +x $(EXECUTABLE_SCRIPT)

bin:
	mkdir -p bin

test: $(EXECUTABLE_SCRIPT)
	@echo "Running Node.js 14 tests..."
	chmod +x tests/run_tests.sh 2>/dev/null || true
	cd tests && ./run_tests.sh

simple-test: $(EXECUTABLE_SCRIPT)
	@echo "Running Node.js 14 simple test..."
	chmod +x tests/simple_test.sh 2>/dev/null || true
	cd tests && ./simple_test.sh

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
	@echo "Installing Node.js 14 dependencies..."
	bash -c "source $(NVM_DIR)/nvm.sh && nvm use $(NODE_VERSION) && npm install"

help:
	@echo "Available targets:"
	@echo "  all         - Build the Node.js 14 benchmark program"
	@echo "  node-version- Show Node.js 14 version information"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple tests"
	@echo "  clean       - Remove built files"
	@echo "  install-nvm - Install Node Version Manager"
	@echo "  setup-node  - Install and setup Node.js 14"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 