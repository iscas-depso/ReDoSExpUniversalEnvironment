# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when collaborating on this repository.

## Project Overview

The **ReDoS Experiment Universal Environment** now centers on delivering a browser-based control plane that orchestrates both ReDoS detection tools and regex engines inside the Docker container. The primary objectives are:

1. Keep all tools and engines pre-built so Docker images remain fast to assemble and predictable in size.
2. Expose an Express-powered API layer plus a single-page dashboard that lets analysts submit regexes, run selected tools in parallel, review generated payloads, and benchmark those payloads against any subset of regex engines.
3. Stream detailed job telemetry (status, stdout/stderr, raw JSON) so failures are observable and workflows remain transparent.


## Project Structure

```
ReDoSExpUniversalEnvironment/
├── tools/              # ReDoS detection tools (6 tools, see below)
├── engines/            # Regex verification engines (19 engines, see below)
├── server/             # Node.js/Express orchestration service (REST + SSE)
├── public/             # Single-page dashboard (HTML/CSS/JS)
├── Dockerfile          # Container definition
├── README.md           # User-focused doc (includes web usage)
├── DEPLOYMENT.md       # Detailed deployment & troubleshooting
└── package.json        # Node service metadata and scripts
```

## Core Workflow (Web-Oriented)

### 1. Detection Stage (`POST /api/jobs/tools`)
- **Input**: Regex string and a list of tool IDs.
- **Behaviour**: Launches each selected tool concurrently; every tool must adhere to the Tool Contract (JSON output written to disk).
- **Output**: A job entry tracked by the server, with progress streamed over Server-Sent Events (SSE) and final JSON payloads returned to the UI.

### 2. Verification Stage (`POST /api/jobs/engines`)
- **Input**: Regex string, encoded attack components from a tool result (prefix, infix, suffix, repeat), a list of engine IDs, and optional overrides (match mode, repeat count, max payload length).
- **Behaviour**: Builds a bounded attack string, executes each engine’s benchmark binary in parallel, and captures stdout/stderr.
- **Output**: Streaming SSE updates per engine containing elapsed time, match counts, and any emitted logs.

### 3. Dashboard (`/public`)
- Renders the two-stage workflow described above.
- Consumes metadata from `/api/meta`, listens to job streams, and surfaces raw JSON/logs for analysts.
- Written in vanilla HTML/CSS/JS to minimize dependencies; any framework introduction needs explicit justification.

## Tool Contract

Every tool provides a `run.py` with the following contract (retain this unchanged):
- **Args**: `<base64_regex> <output_json_path>`
- **Output**: JSON with fields
  ```json
  {
    "elapsed_ms": <number>,
    "is_redos": <boolean>,
    "prefix": "<base64_string>",
    "infix": "<base64_string>",
    "suffix": "<base64_string>",
    "repeat_times": <number or -1>
  }
  ```
- Tools may add extra keys (e.g., diagnostics), but the fields above are mandatory.
- stdout/stderr should remain informative; the web backend truncates long logs but exposes them to users.

## Engine Contract

Every engine exposes a benchmark executable at `bin/benchmark`:
- **Args**: `<base64_regex> <text_file_path> <match_mode>`
  - `match_mode`: `0` for partial match (find all occurrences), `1` for full match.
- **Output (stdout)**: A single line formatted as `{elapsed_ms} - {match_count}` (elapsed time with 6 decimal places, integer match count).
- stderr is reserved for diagnostics; the backend streams it to clients.

## Commands

### Docker
```bash
# Build image (must be rerun after Dockerfile changes)
docker build --rm -t redos-test .

# Run container with dashboard
docker run --rm -p 8080:8080 -v /tmp:/tmp redos-test
```

### Web Service
```bash
# Install dependencies
npm install

# Start local development server with auto-reload
npm run dev

# Quick syntax checks
node --check server/index.js
node --check public/main.js
```

### Tools
```bash
cd tools/<tool_name>
make all        # or tool-specific build
make test       # optional regression tests
python3 run.py <base64_regex> output.json
```

### Engines
```bash
cd engines/<engine_name>
make all
make test
./bin/benchmark <base64_regex> <text_file> <0|1>
```

## Development Strategy & Constraints

### ⚠️ Critical Rule: Rebuild After Dockerfile Changes
- ANY modification to the Dockerfile (new `COPY`, packages, environment changes, etc.) requires an immediate rebuild via `docker build --rm -t redos-test .`.
- Always test within the newly built image; stale images create misleading results.

### Tool/Engine Maintenance
1. Reference the legacy project (`/root/Refactoring/old/ReDoSExpUniversalEnvironment/`) for historical build steps when unsure.
2. Build artifacts locally, then adjust the Dockerfile to `COPY` the runtime outputs instead of compiling in-container.
3. After copying new artifacts, rebuild the image and validate execution inside Docker.
4. Keep contract compliance: do not break the expected CLI arguments or JSON/STDOUT formats.

### Web Service / Frontend Work
1. Preserve API contracts. When changes are unavoidable, update `/public/main.js`, README, and DEPLOYMENT docs together.
2. Use SSE (`/api/jobs/:id/stream`) for progress reporting; avoid introducing redundant polling endpoints unless necessary.
3. Coordinate UI/UX updates with backend behaviour (payload limits, truncation rules, etc.).
4. Keep dependencies lean. Introducing new frameworks/bundlers requires prior discussion and justification.

### Testing Expectations
- **Tools/Engines**: Run their CLI contracts with representative inputs; confirm JSON/STDOUT outputs and error handling.
- **Web Service**: Smoke test via `npm run dev` locally and through containerized execution (`docker run -p 8080:8080 ...`) to ensure end-to-end flows succeed.
- **Automation**: Add Playwright or similar tests only when time/benefit trade-offs make sense; keep them optional.

### Key Considerations
- Maintain fast Docker builds by reusing pre-built binaries and caching Node modules appropriately.
- Mind runtime dependencies (shared libraries, JVMs, .NET runtimes) required by each tool/engine.
- Handle failures gracefully: backend should surface errors without crashing, and UI should keep users informed.
- Optimize for clarity: show attack previews, execution durations, and log snippets to help analysts triage findings quickly.

### Verification Workflow (Chrome DevTools)

- After EVERY change (UI/Backend), open the dashboard in Chrome and validate end‑to‑end behaviour:
  - Static assets (styles.css/main.js) return 200, no stale cache issues.
  - Submit tools run: confirm SSE updates, result cards render with output or error/logs.
  - Pick a tool result via “用于验证”, submit engines run: confirm each engine transitions RUNNING→COMPLETED/FAILED and cards show elapsed/match_count/raw/logs.
  - Long lines in cards must wrap (no overflow); resource-limit inputs must be honoured (time/cores/memory) by backend.

## Working Directory

Unless otherwise specified, operate from `/root/Refactoring/ReDoSExpUniversalEnvironment/` (the designated “main” development directory). Keep this path in mind for all tooling, scripts, and documentation updates. The older snapshot at `/root/Refactoring/old/ReDoSExpUniversalEnvironment/` remains a reference point for build scripts and configurations.
