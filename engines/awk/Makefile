AWK=gawk
TARGET=bin/benchmark
SOURCE=benchmark.awk

.PHONY: all test clean

all: $(TARGET)

$(TARGET): $(SOURCE) | bin
	cp $(SOURCE) $(TARGET)
	chmod +x $(TARGET)

bin:
	mkdir -p bin

test: $(TARGET)
	chmod +x tests/run_tests.sh
	cd tests && ./run_tests.sh

simple-test: $(TARGET)
	chmod +x tests/simple_test.sh
	cd tests && ./simple_test.sh

clean:
	rm -f $(TARGET)
	rmdir bin 2>/dev/null || true

install-deps:
	@echo "Installing dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y gawk; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y gawk; \
	elif command -v apk >/dev/null 2>&1; then \
		apk add --no-cache gawk; \
	else \
		echo "Package manager not found. Please install gawk manually."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Build the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required dependencies"
	@echo "  help        - Show this help message" 