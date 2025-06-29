# =============================================================================
# BASE IMAGE AND ENVIRONMENT CONFIGURATION
# =============================================================================

# Use Ubuntu 22.04 as base image
FROM docker.m.daocloud.io/ubuntu:22.04

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

#################### 代理设置 ####################
# ① 如果你想在 docker build 时临时改地址，只需要
#    docker build --build-arg PROXY=http://其他地址:端口 .
ARG PROXY=http://192.168.1.34:7890

# ② 一次性写全大小写两套环境变量，兼容所有程序
ENV \
    http_proxy=${PROXY} \
    https_proxy=${PROXY} \
    ftp_proxy=${PROXY} \
    HTTP_PROXY=${PROXY} \
    HTTPS_PROXY=${PROXY} \
    FTP_PROXY=${PROXY} \
    # 如果你的 7890 端口同时提供 SOCKS5，可以顺带写上：
    all_proxy=socks5h://192.168.1.34:7890 \
    ALL_PROXY=socks5h://192.168.1.34:7890 \
    # 避免本机回环走代理
    no_proxy=localhost,127.0.0.1,::1 \
    NO_PROXY=localhost,127.0.0.1,::1

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
# TOOLS BUILD AND SETUP
# =============================================================================
# CURSOR RULE: ALL FUTURE TOOL MODIFICATIONS MUST BE ADDED BELOW THIS LINE
# This ensures engines remain unchanged and new tools are built after engines
# =============================================================================

USER root

# =============================================================================
# Install Dependencies
# =============================================================================

RUN apt-get update && apt-get install -y \
    # Java 17 SDK
    --no-install-recommends openjdk-17-jdk-headless  \
    # Maven
    maven \
    # JSON library for C++ tools
    nlohmann-json3-dev

# =============================================================================
# Copy Source Code
# =============================================================================

COPY tools/ /app/tools/


# Set proper ownership
RUN chown -R developer:developer /app


# # =============================================================================
# # Build and Test Rengar tool
# # =============================================================================

# USER developer

# # Build Rengar tool
# WORKDIR /app/tools/rengar
# RUN make all
# # Test Rengar tool
# RUN make test || echo "Rengar tool tests completed"

# # =============================================================================
# # Build and Test ReDoSHunter tool
# # =============================================================================

# USER developer

# # Build ReDoSHunter tool
# WORKDIR /app/tools/redoshunter
# RUN make all
# # Test ReDoSHunter tool
# RUN make test || echo "ReDoSHunter tool tests completed"

# # =============================================================================
# # Build and Test Regulator tool
# # =============================================================================

# USER root

# # Install additional Python packages needed for Regulator
# RUN apt-get update && apt-get install -y \
#     # Additional packages needed for regulator-dynamic
#     libicu-dev \
#     # Install Python 3.8 for Node.js compatibility
#     software-properties-common \
#     && add-apt-repository ppa:deadsnakes/ppa \
#     && apt-get update \
#     && apt-get install -y python3.8 python3.8-dev python3.8-distutils \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python packages for regulator
# RUN python3 -m pip install --no-cache-dir \
#     colored \
#     numpy \
#     scipy \
#     scikit-learn

# USER developer

# # Build Regulator tool
# WORKDIR /app/tools/regulator
# # Take very long time to build and about 130GB memory
# RUN make all -j
# # Test Regulator tool  
# RUN make test || echo "Regulator tool tests completed"


# # =============================================================================
# # Build and Test Regexploit tool
# # =============================================================================

# USER developer

# # Build Regexploit tool
# WORKDIR /app/tools/regexploit
# RUN make all
# # Test Regexploit tool
# RUN make test || echo "Regexploit tool tests completed"

# # =============================================================================
# # Build and Test RegexStatic tool
# # =============================================================================

# USER developer

# # Build RegexStatic tool
# WORKDIR /app/tools/regexstatic
# RUN make all
# # Test RegexStatic tool
# RUN make test || echo "RegexStatic tool tests completed"

# # =============================================================================
# # Build and Test ReScue tool
# # =============================================================================

# USER developer

# # Build ReScue tool
# WORKDIR /app/tools/rescue
# RUN make all
# # Test ReScue tool
# RUN make test || echo "ReScue tool tests completed"

# =============================================================================
# Build and Test GREWIA tool
# =============================================================================

USER developer

# Build GREWIA tool
WORKDIR /app/tools/GREWIA
# Create build directory
RUN mkdir -p build
# Build GREWIA tool
RUN cd build && cmake .. && make -j

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

WORKDIR /app/tools