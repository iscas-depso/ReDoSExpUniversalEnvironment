CC = g++
CFLAGS = -O3 -std=c++11 -Wall -I/usr/local/include
LDFLAGS = -L/usr/local/lib -lhs -lssl -lcrypto -lpthread

SRCDIR = src
BINDIR = bin
TEST_DIR = tests

TARGET = $(BINDIR)/benchmark
SOURCE = $(SRCDIR)/benchmark.cpp

.PHONY: all clean test

all: $(TARGET)

$(BINDIR):
	mkdir -p $(BINDIR)

$(TARGET): $(SOURCE) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -rf $(BINDIR)

test: $(TARGET)
	cd $(TEST_DIR) && ./run_tests.sh

.DEFAULT_GOAL := all 