const fsSync = require('fs');
const fs = require('fs/promises');
const path = require('path');
const util = require('util');
const childProcess = require('child_process');

const execFile = util.promisify(childProcess.execFile);

const { PROJECT_ROOT } = require('./definitions');
const { coresToSpec } = require('./cpu-allocator');

const RUNEXEC_ENV_PATTERNS = [
  'Creating namespace for container mode failed',
  'Operation not permitted',
  'cgroupfs is mounted read-only',
  'Cannot reliably kill sub-processes without freezer cgroup or container mode'
];
const REQUIRED_CONTROLLERS = ['cpu', 'memory', 'pids'];
const RUNEXEC_HINT = 'Start the container with: docker run --rm --privileged --cgroupns=host -p 8080:8080 -v /tmp:/tmp redos-test';

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

function hasRunexecEnvironmentFailure(stdout, stderr) {
  const text = `${stdout || ''}\n${stderr || ''}`;
  return RUNEXEC_ENV_PATTERNS.some(pattern => text.includes(pattern));
}

async function readOptionalFile(filePath) {
  try {
    return await fs.readFile(filePath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
}

async function inspectRunexecEnvironment() {
  const issues = [];
  const mounts = (await readOptionalFile('/proc/mounts')) || '';
  const mountLine = mounts.split(/\r?\n/).find(line => line.split(' ')[1] === '/sys/fs/cgroup');

  let mountType = null;
  let mountOptions = null;
  if (!mountLine) {
    issues.push('/sys/fs/cgroup is not mounted inside the container.');
  } else {
    const parts = mountLine.split(' ');
    mountType = parts[2] || '';
    mountOptions = parts[3] || '';
    if (mountType !== 'cgroup2') {
      issues.push(`/sys/fs/cgroup is mounted as '${mountType}', expected cgroup2.`);
    }
    if (!mountOptions.split(',').includes('rw')) {
      issues.push(`/sys/fs/cgroup is mounted read-only with options '${mountOptions}'.`);
    }
  }

  const controllersRaw = (await readOptionalFile('/sys/fs/cgroup/cgroup.controllers')) || '';
  const controllers = controllersRaw.trim().split(/\s+/).filter(Boolean);
  if (!controllers.length) {
    issues.push('Cannot read any controllers from /sys/fs/cgroup/cgroup.controllers.');
  }

  for (const controller of REQUIRED_CONTROLLERS) {
    if (!controllers.includes(controller)) {
      issues.push(`Required controller '${controller}' is missing from /sys/fs/cgroup/cgroup.controllers.`);
    }
  }

  const requiredPaths = [
    ['/sys/fs/cgroup/cgroup.subtree_control', 'root subtree control file'],
    ['/sys/fs/cgroup/init/cgroup.procs', 'init cgroup.procs'],
    ['/sys/fs/cgroup/benchexec/cgroup.subtree_control', 'benchexec subtree control file']
  ];
  for (const [targetPath, label] of requiredPaths) {
    try {
      await fs.access(targetPath, fsSync.constants.W_OK);
    } catch (error) {
      issues.push(`${label} is not writable (${targetPath}): ${error.message}`);
    }
  }

  const enabledRaw = (await readOptionalFile('/sys/fs/cgroup/benchexec/cgroup.subtree_control')) || '';
  const enabledControllers = enabledRaw.trim().split(/\s+/).filter(Boolean);
  for (const controller of REQUIRED_CONTROLLERS) {
    if (controllers.includes(controller) && !enabledControllers.includes(controller)) {
      issues.push(`Controller '${controller}' is not enabled in /sys/fs/cgroup/benchexec/cgroup.subtree_control.`);
    }
  }

  return {
    issues,
    mountType,
    mountOptions,
    controllers,
    enabledControllers
  };
}

function buildRunexecEnvironmentMessage(diag, extraIssues = []) {
  const issues = [...diag.issues, ...extraIssues].filter(Boolean);
  const uniqueIssues = [...new Set(issues)];
  const lines = ['BenchExec cgroup environment is not ready.'];
  for (const issue of uniqueIssues) {
    lines.push(`- ${issue}`);
  }
  lines.push(`- ${RUNEXEC_HINT}`);
  return lines.join('\n');
}

function buildRunexecEnvironmentError(diag, extraIssues = [], stdout = '', stderr = '') {
  const error = new Error(buildRunexecEnvironmentMessage(diag, extraIssues));
  error.name = 'RunexecEnvironmentError';
  error.code = 'RUNEXEC_ENV_INVALID';
  error.stdout = stdout;
  error.stderr = stderr;
  error.diagnostics = diag;
  return error;
}

async function assertRunexecEnvironment() {
  const diag = await inspectRunexecEnvironment();
  if (diag.issues.length > 0) {
    throw buildRunexecEnvironmentError(diag);
  }
  return diag;
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
  const diag = await assertRunexecEnvironment();

  const ra = [];
  // Always use BenchExec container mode. The service should fail fast if cgroups are unavailable.
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
    if (hasRunexecEnvironmentFailure(stdout, stderr)) {
      const extraIssues = [];
      if (`${stdout}\n${stderr}`.includes('Operation not permitted')) {
        extraIssues.push('Kernel namespace creation was denied by the current container privileges.');
      }
      throw buildRunexecEnvironmentError(diag, extraIssues, stdout, stderr);
    }
    throw error;
  }

  const parsed = parseRunexecResult(stdout);
  if ((parsed.terminationreason === 'failed' || parsed.terminationreason === 'killed')
      && hasRunexecEnvironmentFailure(stdout, stderr)) {
    throw buildRunexecEnvironmentError(diag, [], stdout, stderr);
  }

  return { stdout, stderr, parsed };
}

module.exports = {
  runWithRunexec
};

