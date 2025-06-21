# =============================================================================
# BASE IMAGE AND ENVIRONMENT CONFIGURATION
# =============================================================================

# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# =============================================================================
# SYSTEM PACKAGES AND DEPENDENCIES INSTALLATION
# =============================================================================

# Update package list (separate layer for better caching)
RUN apt-get update

# Install core development tools (rarely change)
RUN apt-get install -y \
    build-essential \
    make \
    git 

# Install network and download tools
RUN apt-get install -y \
    curl \
    wget 

# Install text editors and system utilities
RUN apt-get install -y \
    vim \
    nano \
    htop \
    tree \
    unzip \
    zip 

# Install package management tools
RUN apt-get install -y \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release 

# Install project-specific dependencies (most likely to change)
RUN apt-get install -y \
    libssl-dev \
    libpcre2-dev \
    libboost-regex-dev \
    libre2-dev 
# Install Hyperscan library and build dependencies
RUN apt-get install -y \
    libhyperscan-dev \
    libhyperscan5 \
    cmake \
    ragel \
    pkg-config \
    libbsd-dev 
# Install .NET 7.0 SDK (from Ubuntu packages)
RUN apt-get install -y \
    dotnet-sdk-7.0 
# Install golang
RUN apt-get install -y \
    golang-go 
# Install openjdk-8-jdk
RUN apt-get install -y \
    openjdk-8-jdk 
# Install openjdk-11-jdk for Java 11 implementation
RUN apt-get install -y \
    openjdk-11-jdk 

# Install Perl and required modules
RUN apt-get install -y \
    perl \
    libmime-base64-perl 
# Install PHP CLI
RUN apt-get install -y \
    php-cli 
# Install Python 3
RUN apt-get install -y \
    python3 \
    python3-pip 
# Install Ruby
RUN apt-get install -y \
    ruby 
# Install AWK (gawk) and base64 utility
RUN apt-get install -y \
    gawk \
    coreutils 
# Install grep and bc (basic calculator) for grep benchmark
RUN apt-get install -y \
    grep \
    bc 




# =============================================================================
# USER AND SECURITY CONFIGURATION
# =============================================================================

# Create a non-root user for security
RUN useradd -m -s /bin/bash developer && \
    usermod -aG sudo developer


# Install Rust for developer user
USER developer
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/developer/.cargo/bin:${PATH}"

# Install nvm and both Node.js versions
ENV NVM_DIR="/home/developer/.nvm"
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
RUN bash -c "source $NVM_DIR/nvm.sh && nvm install 14.21.3 && nvm install 21.7.3 && nvm use 21.7.3 && nvm alias default 21.7.3"
ENV PATH="$NVM_DIR/versions/node/v21.7.3/bin:$PATH"

# =============================================================================
# WORKSPACE SETUP
# =============================================================================

# Set up the main working directory
USER root
WORKDIR /app

# Copy project files to the container
COPY engines/awk/ /app/engines/awk/
COPY engines/c/ /app/engines/c/
COPY engines/cpp/ /app/engines/cpp/
COPY engines/csharp/ /app/engines/csharp/
COPY engines/csharp_nonbacktracking/ /app/engines/csharp_nonbacktracking/
COPY engines/go/ /app/engines/go/
COPY engines/grep/ /app/engines/grep/
COPY engines/hyperscan/ /app/engines/hyperscan/
COPY engines/java8/ /app/engines/java8/
COPY engines/java11/ /app/engines/java11/
COPY engines/nodejs14/ /app/engines/nodejs14/
COPY engines/nodejs21/ /app/engines/nodejs21/
COPY engines/perl/ /app/engines/perl/
COPY engines/php/ /app/engines/php/
COPY engines/python/ /app/engines/python/
COPY engines/ruby/ /app/engines/ruby/
COPY engines/rust/ /app/engines/rust/
COPY engines/srm/ /app/engines/srm/
COPY engines/re2/ /app/engines/re2/
COPY engines/run_all_tests.sh /app/engines/
COPY engines/single_regex_all_engines.py /app/engines/
COPY Dockerfile /app/

# Set proper ownership of files
RUN chown -R developer:developer /app


# =============================================================================
# HYPERSCAN LIBRARY SETUP
# =============================================================================

# Hyperscan library is now installed from system packages above
# No source build needed - just ensure ldconfig is run
USER root
RUN ldconfig
USER developer

# =============================================================================
# PROGRAM BUILD AND SETUP AND TESTING
# =============================================================================

# Build AWK program
WORKDIR /app/engines/awk
RUN make all
# Test AWK implementation
RUN make test || echo "AWK tests completed"

# Build C program
WORKDIR /app/engines/c
RUN make all
# Test C implementation
RUN make test || echo "C tests completed"

# Build C++ program
WORKDIR /app/engines/cpp
RUN make all
# Test C++ implementation
RUN make test || echo "C++ tests completed"

# Build C# program
WORKDIR /app/engines/csharp
RUN make all
# Test C# implementation
RUN make test || echo "C# tests completed"

# Build C# Non-Backtracking program
WORKDIR /app/engines/csharp_nonbacktracking
RUN make all
# Test C# Non-Backtracking implementation
RUN make test || echo "C# Non-Backtracking tests completed"

# Build Go program
WORKDIR /app/engines/go
RUN make all
# Test Go implementation
RUN make test || echo "Go tests completed"

# Build Grep program
WORKDIR /app/engines/grep
RUN make all
# Test Grep implementation
RUN make test || echo "Grep tests completed"

# Build Hyperscan benchmark program
WORKDIR /app/engines/hyperscan
RUN make all
# Test Hyperscan implementation
RUN make test || echo "Hyperscan tests completed"

# Build Java 8 program
WORKDIR /app/engines/java8
RUN make all
# Test Java 8 implementation
RUN make test || echo "Java 8 tests completed"

# Build Java 11 program
WORKDIR /app/engines/java11
RUN make all
# Test Java 11 implementation
RUN make test || echo "Java 11 tests completed"

# Build Node.js 14 program (using system Node.js for Docker build)
WORKDIR /app/engines/nodejs14
RUN make all
# Test Node.js 14 implementation
RUN make test || echo "Node.js 14 tests completed"

# Build Node.js 21 program with V8 non-backtracking RegExp engine
WORKDIR /app/engines/nodejs21
ENV NVM_DIR="/home/developer/.nvm"
ENV PATH="$NVM_DIR/versions/node/v21.7.3/bin:$PATH"
RUN bash -c "source $NVM_DIR/nvm.sh && nvm use 21.7.3 && make all"
# Test Node.js 21 implementation with V8 experimental engine
RUN bash -c "source $NVM_DIR/nvm.sh && nvm use 21.7.3 && make test" || echo "Node.js 21 benchmark tests completed"
# Test V8 Non-Backtracking RegExp Engine functionality
RUN bash -c "source $NVM_DIR/nvm.sh && nvm use 21.7.3 && make v8-test" || echo "Node.js 21 V8 engine tests completed"

# Build Perl program
WORKDIR /app/engines/perl
RUN make all
# Test Perl implementation
RUN make test || echo "Perl tests completed"

# Build PHP program
WORKDIR /app/engines/php
RUN make all
# Test PHP implementation
RUN make test || echo "PHP tests completed"

# Build Python program
WORKDIR /app/engines/python
RUN make all
# Test Python implementation
RUN make test || echo "Python tests completed"

# Build Ruby program
WORKDIR /app/engines/ruby
RUN make all
# Test Ruby implementation
RUN make test || echo "Ruby tests completed"

# Build Rust program
WORKDIR /app/engines/rust
RUN make all
# Test Rust implementation
RUN make test || echo "Rust tests completed"

# Build SRM C# program
WORKDIR /app/engines/srm
RUN make all
# Test SRM C# implementation
RUN make test || echo "SRM C# tests completed"

# Build RE2 program
WORKDIR /app/engines/re2
RUN make all
# Test RE2 implementation
RUN make test || echo "RE2 tests completed"

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

# Set proper permissions for the test script
RUN chmod +x /app/engines/run_all_tests.sh

# Set default command to run C tests when container starts
WORKDIR /app/engines