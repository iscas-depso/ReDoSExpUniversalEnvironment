Minimal example to verify runexec works inside a Docker container (container-in-container scenario).

Build:

  docker build -t benchexec-runexec-minimal examples/runexec-docker-minimal

Run test (Linux/macOS shells):

  docker run --rm --privileged --cap-drop=all \
    -v "$PWD":/work -w /work \
    benchexec-runexec-minimal \
    runexec \
      --read-only-dir / \
      --hidden-dir /run --hidden-dir /tmp \
      --full-access-dir /work \
      --dir /work -- /bin/sh /work/examples/runexec-docker-minimal/hello.sh

Notes:
- --read-only-dir / avoids overlay mounts inside Docker (often disallowed).
- --full-access-dir /work gives the working directory write access for the tool.
- --hidden-dir /run and /tmp keep defaults for a clean container view.
- With --full-access-dir /work, files written by the tool under /work
  appear directly in the current host directory (e.g., output.txt, output.log).
