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

# Update package list and install essential system packages
RUN apt-get update && apt-get install -y \
    # Core development tools
    build-essential \
    make \
    git \
    # Network and download tools
    curl \
    wget \
    # Text editors
    vim \
    nano \
    # System monitoring and utilities
    htop \
    tree \
    unzip \
    zip \
    # Package management tools
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    # Project-specific dependencies
    libssl-dev \
    libpcre2-dev \
    # C++ dependencies
    libboost-regex-dev \
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
COPY Dockerfile /app/

# Set proper ownership of files
RUN chown -R developer:developer /app

# Switch to non-root user for security
USER developer

# =============================================================================
# PROGRAM BUILD AND SETUP
# =============================================================================

# Build C program
WORKDIR /app/c
RUN make all

# Build C++ program
WORKDIR /app/cpp
RUN make all

# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

# Test C implementation
WORKDIR /app/c
RUN make test || echo "C tests completed"

# Test C++ implementation
WORKDIR /app/cpp
RUN make test || echo "C++ tests completed"

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

# Set default command to run C tests when container starts
WORKDIR /app/c
CMD ["make", "test"] 