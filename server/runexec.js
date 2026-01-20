const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const util = require('util');
const childProcess = require('child_process');

const execFile = util.promisify(childProcess.execFile);

const { PROJECT_ROOT } = require('./definitions');
const { coresToSpec } = require('./cpu-allocator');

function parseRunexecResult(stdout) {
  const result = {};
  const lines = String(stdout || '').split(/\r?\n/);
  for (const line of lines) {
    const m = line.match(/^(\w+)=([^\n]*)$/);
    if (m) {
      result[m[1]] = m[2];
    }
  }
  return result;
}

function memMbToArg(memoryMB) {
  if (!Number.isFinite(memoryMB) || memoryMB <= 0) return null;
  return `${Math.floor(memoryMB)}MB`;
}

function secondsToArg(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return `${Math.floor(seconds)}s`;
}

async function runWithRunexec({
  cmd,
  args = [],
  cwd,
  env,
  outputLogPath,
  timelimitSeconds,
  walltimelimitSeconds,
  memoryMB,
  cores
}) {
  const runexecPath = path.join(PROJECT_ROOT, 'benchexec', 'bin', 'runexec');
  const pythonBin = process.env.PYTHON_BIN || 'python3';

  const ra = [];
  // Prefer container mode. Allow override via env.
  const noContainer = process.env.RUNEXEC_NO_CONTAINER === '1';
  if (noContainer) {
    ra.push('--no-container');
  }
  // Container-friendly directory model (harmless in no-container mode)
  ra.push('--read-only-dir', '/');
  ra.push('--hidden-dir', '/run');

  ra.push('--full-access-dir', '/tmp');
  ra.push('--full-access-dir', '/app');
  if (outputLogPath) {
    ra.push('--output', outputLogPath);
  }
  const tl = secondsToArg(timelimitSeconds);
  const wl = secondsToArg(walltimelimitSeconds);
  if (tl) ra.push('--timelimit', tl);
  if (wl) ra.push('--walltimelimit', wl);
  const mem = memMbToArg(memoryMB);
  if (mem) ra.push('--memlimit', mem);
  if (Array.isArray(cores) && cores.length > 0) {
    const spec = coresToSpec(cores);
    if (spec) ra.push('--cores', spec);
  }
  if (cwd) {
    ra.push('--dir', cwd);
  }

  ra.push('--', cmd, ...args);

  const execOptions = {
    cwd,
    env: { ...process.env, ...(env || {}) },
    timeout: (walltimelimitSeconds ? (walltimelimitSeconds * 1000 + 5000) : undefined),
    maxBuffer: 20 * 1024 * 1024
  };

  const { stdout, stderr } = await execFile(pythonBin, [runexecPath, ...ra], execOptions);
  const parsed = parseRunexecResult(stdout);
  return { stdout, stderr, parsed };
}

module.exports = {
  runWithRunexec
};

