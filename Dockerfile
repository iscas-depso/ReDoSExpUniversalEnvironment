# =============================================================================
# BASE IMAGE AND ENVIRONMENT CONFIGURATION
# =============================================================================

# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# =============================================================================
# Engines build process
# =============================================================================

# Install all system packages in a single layer
RUN apt-get update && apt-get install -y \
    # Core development tools
    build-essential make git \
    # Network and download tools
    curl wget \
    # Text editors and system utilities
    vim nano htop tree unzip zip \
    # Package management tools
    software-properties-common apt-transport-https ca-certificates gnupg lsb-release \
    # Project-specific dependencies
    libssl-dev libpcre2-dev libboost-regex-dev libre2-dev \
    # Hyperscan library and build dependencies
    libhyperscan-dev libhyperscan5 cmake ragel pkg-config libbsd-dev \
    # .NET 7.0 SDK
    dotnet-sdk-7.0 \
    # Golang
    golang-go \
    # Java SDKs
    openjdk-8-jdk openjdk-11-jdk\
    # Perl and modules
    perl libmime-base64-perl \
    # PHP CLI
    php-cli \
    # Python 3
    python3 python3-pip \
    # Ruby
    ruby \
    # AWK and utilities
    gawk coreutils \
    # Grep and calculator
    grep bc \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Create a non-root user for security
RUN useradd -m -s /bin/bash developer && \
    usermod -aG sudo developer

# Install Rust, nvm and Node.js for developer user
USER developer
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/developer/.cargo/bin:${PATH}"

ENV NVM_DIR="/home/developer/.nvm"
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash && \
    bash -c "source $NVM_DIR/nvm.sh && nvm install 14.21.3 && nvm install 21.7.3 && nvm use 21.7.3 && nvm alias default 21.7.3"
ENV PATH="$NVM_DIR/versions/node/v21.7.3/bin:$PATH"

USER root
WORKDIR /app

# Copy all project files
COPY engines/ /app/engines/
COPY Dockerfile /app/

# Set proper ownership
RUN chown -R developer:developer /app && \
    chmod +x /app/engines/run_all_tests.sh

USER developer

# Build all engines in consolidated layers
RUN cd /app/engines && \
    # Build compiled engines
    (cd awk && make all) && \
    (cd c && make all) && \
    (cd cpp && make all) && \
    (cd csharp && make all) && \
    (cd csharp_nonbacktracking && make all) && \
    (cd go && make all) && \
    (cd grep && make all) && \
    (cd hyperscan && make all) && \
    (cd java8 && make all) && \
    (cd java11 && make all) && \
    (cd perl && make all) && \
    (cd php && make all) && \
    (cd python && make all) && \
    (cd ruby && make all) && \
    (cd rust && make all) && \
    (cd srm && make all) && \
    (cd re2 && make all) && \
    # Build Node.js engines with proper environment
    (cd nodejs14 && make all) && \
    (cd nodejs21 && bash -c "source $NVM_DIR/nvm.sh && nvm use 21.7.3 && make all")

# Test all engines in consolidated layer
RUN cd /app/engines && \
    # Test all engines (allow failures to continue)
    (cd awk && make test || echo "AWK tests completed") && \
    (cd c && make test || echo "C tests completed") && \
    (cd cpp && make test || echo "C++ tests completed") && \
    (cd csharp && make test || echo "C# tests completed") && \
    (cd csharp_nonbacktracking && make test || echo "C# Non-Backtracking tests completed") && \
    (cd go && make test || echo "Go tests completed") && \
    (cd grep && make test || echo "Grep tests completed") && \
    (cd hyperscan && make test || echo "Hyperscan tests completed") && \
    (cd java8 && make test || echo "Java 8 tests completed") && \
    (cd java11 && make test || echo "Java 11 tests completed") && \
    (cd nodejs14 && make test || echo "Node.js 14 tests completed") && \
    (cd nodejs21 && bash -c "source $NVM_DIR/nvm.sh && nvm use 21.7.3 && make test && make v8-test" || echo "Node.js 21 tests completed") && \
    (cd perl && make test || echo "Perl tests completed") && \
    (cd php && make test || echo "PHP tests completed") && \
    (cd python && make test || echo "Python tests completed") && \
    (cd ruby && make test || echo "Ruby tests completed") && \
    (cd rust && make test || echo "Rust tests completed") && \
    (cd srm && make test || echo "SRM C# tests completed") && \
    (cd re2 && make test || echo "RE2 tests completed")


# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

WORKDIR /app/engines