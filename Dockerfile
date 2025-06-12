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
    git \
    && rm -rf /var/lib/apt/lists/*

# Install network and download tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install text editors and system utilities
RUN apt-get update && apt-get install -y \
    vim \
    nano \
    htop \
    tree \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install package management tools
RUN apt-get update && apt-get install -y \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install project-specific dependencies (most likely to change)
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libpcre2-dev \
    libboost-regex-dev \
    && rm -rf /var/lib/apt/lists/*
# Install .NET 7.0 SDK (from Ubuntu packages)
RUN apt-get update && apt-get install -y \
    dotnet-sdk-7.0 \
    && rm -rf /var/lib/apt/lists/*
# Install golang
RUN apt-get update && apt-get install -y \
    golang-go \
    && rm -rf /var/lib/apt/lists/*
# Install openjdk-8-jdk
RUN apt-get update && apt-get install -y \
    openjdk-8-jdk \
    && rm -rf /var/lib/apt/lists/*
# Install openjdk-11-jdk for Java 11 implementation
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    && rm -rf /var/lib/apt/lists/*
# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*
# Install curl for nvm installation
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Install Perl and required modules
RUN apt-get update && apt-get install -y \
    perl \
    libmime-base64-perl \
    && rm -rf /var/lib/apt/lists/*
# Install PHP CLI
RUN apt-get update && apt-get install -y \
    php-cli \
    && rm -rf /var/lib/apt/lists/*
# Install Python 3
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
# Install Ruby
RUN apt-get update && apt-get install -y \
    ruby \
    && rm -rf /var/lib/apt/lists/*
# Install Rust (will be installed for developer user later)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# USER AND SECURITY CONFIGURATION
# =============================================================================

# Create a non-root user for security
RUN useradd -m -s /bin/bash developer && \
    usermod -aG sudo developer

# =============================================================================
# WORKSPACE SETUP
# =============================================================================

# Set up the main working directory
WORKDIR /app

# Copy project files to the container
COPY c/ /app/c/
COPY cpp/ /app/cpp/
COPY csharp/ /app/csharp/
COPY csharp_nonbacktracking/ /app/csharp_nonbacktracking/
COPY go/ /app/go/
COPY java8/ /app/java8/
COPY java11/ /app/java11/
COPY nodejs14/ /app/nodejs14/
COPY nodejs21/ /app/nodejs21/
COPY perl/ /app/perl/
COPY php/ /app/php/
COPY python/ /app/python/
COPY ruby/ /app/ruby/
COPY rust/ /app/rust/
COPY srm/ /app/srm/
COPY Dockerfile /app/

# Set proper ownership of files
RUN chown -R developer:developer /app

# Install Rust for developer user
USER developer
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/developer/.cargo/bin:${PATH}"
USER root

# Switch to non-root user for security
USER developer

# =============================================================================
# PROGRAM BUILD AND SETUP AND TESTING
# =============================================================================

# Build C program
WORKDIR /app/c
RUN make all
# Test C implementation
RUN make test || echo "C tests completed"

# Build C++ program
WORKDIR /app/cpp
RUN make all
# Test C++ implementation
RUN make test || echo "C++ tests completed"

# Build C# program
WORKDIR /app/csharp
RUN make all
# Test C# implementation
RUN make test || echo "C# tests completed"

# Build C# Non-Backtracking program
WORKDIR /app/csharp_nonbacktracking
RUN make all
# Test C# Non-Backtracking implementation
RUN make test || echo "C# Non-Backtracking tests completed"

# Build Go program
WORKDIR /app/go
RUN make all
# Test Go implementation
RUN make test || echo "Go tests completed"

# Build Java 8 program
WORKDIR /app/java8
RUN make all
# Test Java 8 implementation
RUN make test || echo "Java 8 tests completed"

# Build Java 11 program
WORKDIR /app/java11
RUN make all
# Test Java 11 implementation
RUN make test || echo "Java 11 tests completed"

# Build Node.js 14 program (using system Node.js for Docker build)
WORKDIR /app/nodejs14
RUN make all
# Test Node.js 14 implementation
RUN make test || echo "Node.js 14 tests completed"

# Build Node.js 21 program (using system Node.js for Docker build)
WORKDIR /app/nodejs21
RUN make all
# Test Node.js 21 implementation  
RUN make test || echo "Node.js 21 tests completed"

# Build Perl program
WORKDIR /app/perl
RUN make all
# Test Perl implementation
RUN make test || echo "Perl tests completed"

# Build PHP program
WORKDIR /app/php
RUN make all
# Test PHP implementation
RUN make test || echo "PHP tests completed"

# Build Python program
WORKDIR /app/python
RUN make all
# Test Python implementation
RUN make test || echo "Python tests completed"

# Build Ruby program
WORKDIR /app/ruby
RUN make all
# Test Ruby implementation
RUN make test || echo "Ruby tests completed"

# Build Rust program
WORKDIR /app/rust
RUN make all
# Test Rust implementation
RUN make test || echo "Rust tests completed"

# Build SRM C# program
WORKDIR /app/srm
RUN make all
# Test SRM C# implementation
RUN make test || echo "SRM C# tests completed"

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

# Set default command to run C tests when container starts
WORKDIR /app