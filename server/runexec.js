const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const util = require('util');
const childProcess = require('child_process');

const execFile = util.promisify(childProcess.execFile);

const { PROJECT_ROOT } = require('./definitions');
const { coresToSpec } = require('./cpu-allocator');

const RUNEXEC_FALLBACK_PATTERNS = [
  'Creating namespace for container mode failed',
  'Operation not permitted',
  'cgroupfs is mounted read-only',
  'Cannot reliably kill sub-processes without freezer cgroup or container mode'
];

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

function isRunexecUnavailableOutput(stdout, stderr) {
  const text = `${stdout || ''}\n${stderr || ''}`;
  return RUNEXEC_FALLBACK_PATTERNS.some(pattern => text.includes(pattern));
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

  let stdout = '';
  let stderr = '';
  try {
    const result = await execFile(pythonBin, [runexecPath, ...ra], execOptions);
    stdout = result.stdout || '';
    stderr = result.stderr || '';
  } catch (error) {
    stdout = error.stdout || '';
    stderr = error.stderr || '';
    if (isRunexecUnavailableOutput(stdout, stderr)) {
      const fallbackError = new Error('runexec is unavailable in the current container environment');
      fallbackError.code = 'RUNEXEC_UNAVAILABLE';
      fallbackError.stdout = stdout;
      fallbackError.stderr = stderr;
      throw fallbackError;
    }
    throw error;
  }

  const parsed = parseRunexecResult(stdout);
  if ((parsed.terminationreason === 'failed' || parsed.terminationreason === 'killed')
      && isRunexecUnavailableOutput(stdout, stderr)) {
    const fallbackError = new Error('runexec is unavailable in the current container environment');
    fallbackError.code = 'RUNEXEC_UNAVAILABLE';
    fallbackError.stdout = stdout;
    fallbackError.stderr = stderr;
    fallbackError.parsed = parsed;
    throw fallbackError;
  }

  return { stdout, stderr, parsed };
}

module.exports = {
  runWithRunexec
};
