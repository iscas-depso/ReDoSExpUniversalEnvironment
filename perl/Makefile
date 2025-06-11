PERL=perl
TARGET=bin/benchmark
SOURCE=benchmark.pl

.PHONY: all test clean install-deps help

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
	@echo "Installing Perl dependencies..."
	@if command -v cpan >/dev/null 2>&1; then \
		cpan -i MIME::Base64 Time::HiRes; \
	elif command -v cpanm >/dev/null 2>&1; then \
		cpanm MIME::Base64 Time::HiRes; \
	elif command -v apt-get >/dev/null 2>&1; then \
		apt-get update && apt-get install -y libmime-base64-perl; \
	elif command -v yum >/dev/null 2>&1; then \
		yum install -y perl-MIME-Base64; \
	else \
		echo "Package manager not found. Please install MIME::Base64 and Time::HiRes manually."; \
		echo "Most Perl installations include these modules by default."; \
	fi

help:
	@echo "Available targets:"
	@echo "  all         - Prepare the benchmark program"
	@echo "  test        - Run all tests"
	@echo "  simple-test - Run simple test"
	@echo "  clean       - Remove built files"
	@echo "  install-deps- Install required Perl dependencies"
	@echo "  help        - Show this help message" 