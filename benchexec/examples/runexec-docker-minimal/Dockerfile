FROM python:3.11-slim

# Install BenchExec
RUN pip install --no-cache-dir benchexec \
    && mkdir -p /work /out

# Default workdir for convenience (will be overridden by -w /work when running)
WORKDIR /work

# No entrypoint; we invoke runexec directly in docker run

