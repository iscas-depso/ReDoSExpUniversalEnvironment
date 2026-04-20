# =============================================================================
# BASE IMAGE AND ENVIRONMENT CONFIGURATION
# =============================================================================

# Use Ubuntu 22.04 as base image (use China mirror if DockerHub is blocked)
# To use mirror: docker build --build-arg BASE_IMAGE=docker.1ms.run/library/ubuntu:22.04 .
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

#################### 代理设置 ####################
# 如果你想在 docker build 时临时改地址，可使用：
#    docker build --build-arg PROXY=http://其他地址:端口 .
ARG PROXY=

# 一次性写全大小写两套环境变量，兼容所有程序
ENV \
    http_proxy=${PROXY} \
    https_proxy=${PROXY} \
    ftp_proxy=${PROXY} \
    HTTP_PROXY=${PROXY} \
    HTTPS_PROXY=${PROXY} \
    FTP_PROXY=${PROXY} \
    all_proxy=${PROXY} \
    ALL_PROXY=${PROXY} \
    no_proxy=localhost,127.0.0.1,::1 \
    NO_PROXY=localhost,127.0.0.1,::1

# =============================================================================
# SYSTEM PACKAGES INSTALLATION
# =============================================================================

# Install all system packages in single layer
RUN apt-get update && apt-get install -y \
    # Core development tools
    build-essential make git \
    # Network and download tools
    curl wget \
    # Text editors and system utilities
    vim nano htop tree unzip zip \
    # Package management tools
    software-properties-common apt-transport-https ca-certificates gnupg lsb-release \
    # Python 3 and pip
    python3 python3-pip \
    # C engine runtime dependencies
    libpcre2-8-0 libssl3 \
    # C++ engine runtime dependencies (boost regex and ICU)
    libboost-regex1.74.0 libicu70 \
    # re2 and hyperscan engines
    libre2-9 libhyperscan5 \
    # Perl, PHP, Ruby interpreters
    perl php-cli ruby \
    # awk and grep engines
    gawk grep \
    # Java runtime (OpenJDK 8, 11, and 17 for rengar)
    openjdk-8-jre openjdk-11-jre openjdk-17-jre \
    && rm -rf /var/lib/apt/lists/*

# Install .NET 7.0 runtime for C# engines
RUN curl -sSL https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -o /tmp/packages-microsoft-prod.deb && \
    dpkg -i /tmp/packages-microsoft-prod.deb && \
    rm /tmp/packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y aspnetcore-runtime-7.0 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash developer && \
    usermod -aG sudo developer

# =============================================================================
# NODE.JS SETUP WITH NVM
# =============================================================================

# Install nvm and Node.js versions for developer user
USER developer
ENV NVM_DIR="/home/developer/.nvm"
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash && \
    bash -c "source $NVM_DIR/nvm.sh && nvm install 14.21.3 && nvm install 21.7.3 && nvm use 21.7.3 && nvm alias default 21.7.3"
ENV PATH="$NVM_DIR/versions/node/v21.7.3/bin:$PATH"

# =============================================================================
# TOOLS BUILD AND SETUP
# =============================================================================

USER root
WORKDIR /app

# Copy regexploit tool
COPY tools/regexploit/ /app/tools/regexploit/

# Install regexploit (Python package)
RUN cd /app/tools/regexploit/src && python3 -m pip install -e . --no-deps

# Install Python dependencies for regulator tool and BenchExec for resource limits
RUN python3 -m pip install --no-cache-dir colored numpy scipy scikit-learn benchexec

# Copy regexstatic tool (pre-built JAR and dependencies)
COPY tools/regexstatic/ /app/tools/regexstatic/

# Copy rescue tool (pre-built fat JAR)
COPY tools/rescue/ /app/tools/rescue/

# Copy rengar tool (pre-built fat JAR, requires Java 17)
COPY tools/rengar/ /app/tools/rengar/

# Copy redoshunter tool (pre-built GraalVM native image)
COPY tools/redoshunter/ /app/tools/redoshunter/

# Copy regulator tool (pre-built V8-based fuzzer)
COPY tools/regulator/ /app/tools/regulator/

# Copy Python engine (pre-built)
COPY engines/python/ /app/engines/python/

# Copy C engine (pre-built with PCRE2)
COPY engines/c/ /app/engines/c/

# Copy Perl engine (pre-built script)
COPY engines/perl/ /app/engines/perl/

# Copy PHP engine (pre-built script)
COPY engines/php/ /app/engines/php/

# Copy Ruby engine (pre-built script)
COPY engines/ruby/ /app/engines/ruby/

# Copy Go engine (pre-built static binary)
COPY engines/go/ /app/engines/go/

# Copy Rust engine (pre-built binary)
COPY engines/rust/ /app/engines/rust/

# Copy awk engine (script)
COPY engines/awk/ /app/engines/awk/

# Copy grep engine (script)
COPY engines/grep/ /app/engines/grep/

# Copy C++ engine (pre-built with Boost)
COPY engines/cpp/ /app/engines/cpp/

# Copy re2 engine (pre-built binary)
COPY engines/re2/ /app/engines/re2/

# Copy hyperscan engine (pre-built binary)
COPY engines/hyperscan/ /app/engines/hyperscan/

# Copy Node.js engines (scripts)
COPY engines/nodejs14/ /app/engines/nodejs14/
COPY engines/nodejs21/ /app/engines/nodejs21/

# Remove UTF-8 BOM from nodejs benchmark scripts (prevents "not found" errors on Linux)
RUN sed -i '1s/^\xEF\xBB\xBF//' /app/engines/nodejs14/bin/benchmark /app/engines/nodejs21/bin/benchmark 2>/dev/null || true

# Copy Java engines (pre-compiled bytecode)
COPY engines/java8/ /app/engines/java8/
COPY engines/java11/ /app/engines/java11/

# Copy C# engines (framework-dependent binaries)
COPY engines/csharp/ /app/engines/csharp/
COPY engines/csharp_nonbacktracking/ /app/engines/csharp_nonbacktracking/
COPY engines/srm/ /app/engines/srm/

# Copy web interface assets and server
COPY package.json package-lock.json /app/
COPY public/ /app/public/
COPY server/ /app/server/
COPY init.sh /init.sh
RUN chmod +x /init.sh
COPY benchexec/ /app/benchexec/

# Ensure Node.js binaries are available system-wide without depending on /home paths.
# BenchExec container mode may isolate /home, so copy the actual binaries instead of symlinking.
RUN install -m 0755 /home/developer/.nvm/versions/node/v14.21.3/bin/node /usr/local/bin/node14 \
 && install -m 0755 /home/developer/.nvm/versions/node/v21.7.3/bin/node /usr/local/bin/node21 \
 && install -m 0755 /home/developer/.nvm/versions/node/v21.7.3/bin/node /usr/local/bin/node

# Change ownership to developer
RUN chown -R developer:developer /app

USER developer

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

WORKDIR /app

# Install node dependencies for the web service
RUN npm ci --omit=dev

EXPOSE 8080
USER root
ENTRYPOINT ["/init.sh"]
CMD ["npm", "start"]
