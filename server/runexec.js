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
  'Cannot reliably kill sub-processes without freezer cgroup or container mode',
  'No space left on device'
];
const REQUIRED_CONTROLLERS = ['cpu', 'memory', 'pids'];
const RUNEXEC_HINT = 'Start the container with: docker run --rm --privileged --cgroupns=host -p 8080:8080 -v /tmp:/tmp redos-test';
const BENCH_EXEC_CGROUP_ROOT = '/sys/fs/cgroup/benchexec';
const BENCH_EXEC_CGROUP_PREFIX = 'benchexec_';
const BENCH_EXEC_CGROUP_CLEANUP_THRESHOLD = 64;
const BENCH_EXEC_CGROUP_MIN_AGE_MS = 30_000;
const BENCH_EXEC_CGROUP_FORCE_MIN_AGE_MS = 5_000;
const RUNEXEC_EXEC_TIMEOUT_GRACE_MS = 10 * 60 * 1000;

let cleanupQueue = Promise.resolve();

function isIgnorableCgroupFsError(error) {
  return ['ENOENT', 'ENODEV', 'ESTALE', 'ENXIO'].includes(error?.code);
}

function parseRunexecResult(text) {
  const result = {};
  const lines = String(text || '').split(/\r?\n/);
  for (const line of lines) {
    const m = line.match(/^(\w+)=([^\n]*)$/);
    if (m) {
      result[m[1]] = m[2];
    }
  }
  return result;
}

function parseRunexecStreams(stdout, stderr) {
  return normalizeRunexecParsed(parseRunexecResult(`${stdout || ''}\n${stderr || ''}`));
}

async function parseRunexecStreamsWithOutputLog(stdout, stderr, outputLogPath) {
  const outputLog = outputLogPath ? (await readOptionalFile(outputLogPath)) : '';
  return {
    parsed: normalizeRunexecParsed(parseRunexecResult(`${stdout || ''}\n${stderr || ''}\n${outputLog || ''}`)),
    outputLog: outputLog || ''
  };
}

function normalizeRunexecParsed(parsed) {
  const returnValue = Number(parsed?.returnvalue);
  return {
    ...parsed,
    returnValue: Number.isFinite(returnValue) ? returnValue : null,
    terminationReason: parsed?.terminationreason || null
  };
}

function hasRunexecEnvironmentFailure(stdout, stderr) {
  const text = `${stdout || ''}\n${stderr || ''}`;
  return RUNEXEC_ENV_PATTERNS.some(pattern => text.includes(pattern));
}

function hasNoSpaceLeftOnDevice(stdout, stderr, message = '') {
  const text = `${stdout || ''}\n${stderr || ''}\n${message || ''}`;
  return text.includes('No space left on device');
}

async function readOptionalFile(filePath) {
  try {
    return await fs.readFile(filePath, 'utf8');
  } catch (error) {
    if (isIgnorableCgroupFsError(error)) {
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

async function readCgroupEvents(dirPath) {
  const eventsPath = path.join(dirPath, 'cgroup.events');
  const raw = await readOptionalFile(eventsPath);
  if (!raw) {
    return {};
  }
  const events = {};
  for (const line of raw.split(/\r?\n/)) {
    const [key, value] = line.trim().split(/\s+/, 2);
    if (key && value) {
      events[key] = value;
    }
  }
  return events;
}

async function readCgroupProcCount(dirPath) {
  let count = 0;
  for (const fileName of ['cgroup.procs', 'cgroup.threads']) {
    const raw = await readOptionalFile(path.join(dirPath, fileName));
    if (!raw) {
      continue;
    }
    count += raw.split(/\r?\n/).filter(Boolean).length;
  }
  return count;
}

async function collectChildCgroupDirs(dirPath) {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    return entries
      .filter(entry => entry.isDirectory())
      .map(entry => path.join(dirPath, entry.name));
  } catch (error) {
    if (isIgnorableCgroupFsError(error) || error.code === 'EACCES' || error.code === 'EPERM') {
      return [];
    }
    throw error;
  }
}

async function subtreeHasActiveProcesses(dirPath) {
  const procCount = await readCgroupProcCount(dirPath);
  if (procCount > 0) {
    return true;
  }

  const events = await readCgroupEvents(dirPath);
  if (events.populated && events.populated !== '0') {
    return true;
  }

  const children = await collectChildCgroupDirs(dirPath);
  for (const childPath of children) {
    if (await subtreeHasActiveProcesses(childPath)) {
      return true;
    }
  }
  return false;
}

async function removeInactiveBenchExecTree(dirPath, { allowFileCleanup = false } = {}) {
  const children = await collectChildCgroupDirs(dirPath);
  let removed = 0;
  for (const childPath of children) {
    removed += await removeInactiveBenchExecTree(childPath, { allowFileCleanup });
  }

  try {
    await fs.rmdir(dirPath);
    return removed + 1;
  } catch (error) {
    if (error.code === 'ENOTEMPTY' && allowFileCleanup) {
      await fs.rm(dirPath, { recursive: true, force: true });
      return removed + 1;
    }
    if (isIgnorableCgroupFsError(error) || ['ENOTEMPTY', 'EBUSY', 'EACCES', 'EPERM'].includes(error.code)) {
      return removed;
    }
    throw error;
  }
}

async function isBenchExecDirOldEnough(dirPath, minAgeMs) {
  if (!Number.isFinite(minAgeMs) || minAgeMs <= 0) {
    return true;
  }
  try {
    const stat = await fs.stat(dirPath);
    return (Date.now() - stat.mtimeMs) >= minAgeMs;
  } catch (error) {
    if (isIgnorableCgroupFsError(error) || error.code === 'EACCES' || error.code === 'EPERM') {
      return false;
    }
    throw error;
  }
}

async function removeStaleBenchExecTree(dirPath, { allowFileCleanup = false } = {}) {
  if (await subtreeHasActiveProcesses(dirPath)) {
    return 0;
  }
  return removeInactiveBenchExecTree(dirPath, { allowFileCleanup });
}

async function countBenchExecRoots(rootPath = BENCH_EXEC_CGROUP_ROOT) {
  try {
    const entries = await fs.readdir(rootPath, { withFileTypes: true });
    return entries.filter(entry => entry.isDirectory() && entry.name.startsWith(BENCH_EXEC_CGROUP_PREFIX)).length;
  } catch (error) {
    if (isIgnorableCgroupFsError(error) || error.code === 'EACCES' || error.code === 'EPERM') {
      return 0;
    }
    throw error;
  }
}

async function cleanupStaleBenchExecCgroups({
  force = false,
  rootPath = BENCH_EXEC_CGROUP_ROOT,
  allowFileCleanup = false,
  minAgeMs = force ? BENCH_EXEC_CGROUP_FORCE_MIN_AGE_MS : BENCH_EXEC_CGROUP_MIN_AGE_MS
} = {}) {
  cleanupQueue = cleanupQueue.catch(() => {}).then(async () => {
    let topLevelDirs;
    try {
      const entries = await fs.readdir(rootPath, { withFileTypes: true });
      topLevelDirs = entries
        .filter(entry => entry.isDirectory() && entry.name.startsWith(BENCH_EXEC_CGROUP_PREFIX))
        .map(entry => path.join(rootPath, entry.name));
    } catch (error) {
      if (isIgnorableCgroupFsError(error) || error.code === 'EACCES' || error.code === 'EPERM') {
        return { removed: 0, remaining: 0 };
      }
      throw error;
    }

    if (!force && topLevelDirs.length < BENCH_EXEC_CGROUP_CLEANUP_THRESHOLD) {
      return { removed: 0, remaining: topLevelDirs.length };
    }

    let removed = 0;
    for (const dirPath of topLevelDirs) {
      if (!(await isBenchExecDirOldEnough(dirPath, minAgeMs))) {
        continue;
      }
      removed += await removeStaleBenchExecTree(dirPath, { allowFileCleanup });
    }
    const remaining = await countBenchExecRoots(rootPath);
    return { removed, remaining };
  });

  return cleanupQueue;
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

function computeExecTimeoutMs(walltimelimitSeconds) {
  if (!Number.isFinite(walltimelimitSeconds) || walltimelimitSeconds <= 0) {
    return undefined;
  }
  return Math.ceil(walltimelimitSeconds * 1000 + RUNEXEC_EXEC_TIMEOUT_GRACE_MS);
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
  await cleanupStaleBenchExecCgroups();
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
    // BenchExec may need substantial extra time after the wrapped tool exits in
    // order to tear down container/cgroup state and emit the final summary.
    timeout: computeExecTimeoutMs(walltimelimitSeconds),
    maxBuffer: 20 * 1024 * 1024
  };

  let stdout = '';
  let stderr = '';
  let parsed = normalizeRunexecParsed({});
  let runexecOutputLog = '';
  const invokeRunexec = async () => {
    const result = await execFile(pythonBin, [runexecPath, ...ra], execOptions);
    stdout = result.stdout || '';
    stderr = result.stderr || '';
    const parsedStreams = await parseRunexecStreamsWithOutputLog(stdout, stderr, outputLogPath);
    parsed = parsedStreams.parsed;
    runexecOutputLog = parsedStreams.outputLog;
  };

  try {
    await invokeRunexec();
  } catch (error) {
    stdout = error.stdout || '';
    stderr = error.stderr || '';
    const parsedStreams = await parseRunexecStreamsWithOutputLog(stdout, stderr, outputLogPath);
    parsed = parsedStreams.parsed;
    runexecOutputLog = parsedStreams.outputLog;

    if (hasNoSpaceLeftOnDevice(stdout, stderr, error.message)) {
      await cleanupStaleBenchExecCgroups({ force: true });
      try {
        await invokeRunexec();
      } catch (retryError) {
        stdout = retryError.stdout || '';
        stderr = retryError.stderr || '';
        const retryParsedStreams = await parseRunexecStreamsWithOutputLog(stdout, stderr, outputLogPath);
        parsed = retryParsedStreams.parsed;
        runexecOutputLog = retryParsedStreams.outputLog;
        if (hasRunexecEnvironmentFailure(stdout, stderr)) {
          const extraIssues = [];
          if (`${stdout}\n${stderr}`.includes('Operation not permitted')) {
            extraIssues.push('Kernel namespace creation was denied by the current container privileges.');
          }
          if (hasNoSpaceLeftOnDevice(stdout, stderr, retryError.message)) {
            extraIssues.push('BenchExec cgroup creation failed because stale cgroup directories exhausted the cgroup filesystem.');
          }
          throw buildRunexecEnvironmentError(diag, extraIssues, stdout, stderr);
        }
        throw Object.assign(new Error(retryError.message || 'runexec failed'), {
          code: retryError.code,
          stdout,
          stderr,
          outputLog: runexecOutputLog,
          parsed
        });
      }
    } else if (hasRunexecEnvironmentFailure(stdout, stderr)) {
      const extraIssues = [];
      if (`${stdout}\n${stderr}`.includes('Operation not permitted')) {
        extraIssues.push('Kernel namespace creation was denied by the current container privileges.');
      }
      throw buildRunexecEnvironmentError(diag, extraIssues, stdout, stderr);
    } else {
      throw Object.assign(new Error(error.message || 'runexec failed'), {
        code: error.code,
        stdout,
        stderr,
        outputLog: runexecOutputLog,
        parsed
      });
    }
  } finally {
    await cleanupStaleBenchExecCgroups();
  }

  if ((parsed.terminationReason === 'failed' || parsed.terminationReason === 'killed')
      && hasRunexecEnvironmentFailure(stdout, stderr)) {
    throw buildRunexecEnvironmentError(diag, [], stdout, stderr);
  }

  return { stdout, stderr, outputLog: runexecOutputLog, parsed };
}

module.exports = {
  runWithRunexec,
  cleanupStaleBenchExecCgroups,
  computeExecTimeoutMs,
  parseRunexecResult,
  parseRunexecStreams,
  parseRunexecStreamsWithOutputLog
};

