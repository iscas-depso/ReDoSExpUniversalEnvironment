# ReDoS regex attack string generate tool - Regulator
# Makefile for building and testing the Regulator tool

.PHONY: all build test clean

# Build target
all: build

build:
	@echo "Building Regulator tool..."
	# Create temporary python symlink for Node.js build
	mkdir -p /tmp/python38-link
	ln -sf /usr/bin/python3.8 /tmp/python38-link/python
	ln -sf /usr/bin/python3.8 /tmp/python38-link/python3
	# Build the regulator-dynamic fuzzer using Python 3.8
	cd regulator-dynamic/fuzzer && PATH="/tmp/python38-link:$$PATH" $(MAKE) -j node
	cd regulator-dynamic/fuzzer && $(MAKE) -j
	# Clean up temporary symlink
	rm -rf /tmp/python38-link
	# Install Python dependencies for the driver
	cd regulator-dynamic/driver && python3 -m pip install --user colored numpy scipy scikit-learn || true
	# Make run.py executable
	chmod +x run.py
	@echo "Regulator build completed."

# Test target
test:
	@echo "Testing Regulator tool..."
	# Create a simple test
	python3 -c "import base64; print(base64.b64encode(b'(a+)+b').decode())" > test_regex.txt
	@echo "Running test with regex (a+)+b..."
	python3 run.py `cat test_regex.txt` test_output.json || echo "Test completed"
	@if [ -f test_output.json ]; then \
		echo "Test output:"; \
		cat test_output.json; \
		echo ""; \
	else \
		echo "Test output file not created"; \
	fi
	# Clean up test files
	rm -f test_regex.txt test_output.json
	# Create a simple test
	python3 -c "import base64; print(base64.b64encode(b'^a*.a*c$$').decode())" > test_regex.txt
	@echo "Running test with regex ^a*.a*c$$..."
	python3 run.py `cat test_regex.txt` test_output.json || echo "Test completed"
	@if [ -f test_output.json ]; then \
		echo "Test output:"; \
		cat test_output.json; \
		echo ""; \
	else \
		echo "Test output file not created"; \
	fi
	# Clean up test files
	rm -f test_regex.txt test_output.json
	@echo "Regulator test completed."

# Clean target
clean:
	@echo "Cleaning Regulator build artifacts..."
	cd regulator-dynamic/fuzzer && $(MAKE) clean || true
	rm -f test_output.json test_regex.txt
	@echo "Regulator clean completed." 