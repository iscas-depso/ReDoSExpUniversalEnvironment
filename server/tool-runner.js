const fs = require('fs/promises');
const os = require('os');
const path = require('path');

const { TOOL_DEFINITIONS } = require('./definitions');
const { runWithRunexec } = require('./runexec');

const LOG_LIMIT = 4000;
const TOOL_TIMEOUT_GRACE_SECONDS = 15;
const MAX_INFRA_RETRIES = 3;
const TOOL_EXCEPTION_PATTERNS = [
  'StackOverflowError',
  'Exception in thread',
  'Traceback (most recent call last):',
  'UnicodeDecodeError',
  'SyntaxError:',
  'Unhandled exception'
];

function parseRunexecTimeToMs(value) {
  if (!value) {
    return null;
  }
  const text = String(value).trim();
  const match = text.match(/^(-?\d+(?:\.\d+)?)(ms|s)?$/);
  if (!match) {
    return null;
  }
  const amount = Number(match[1]);
  if (!Number.isFinite(amount)) {
    return null;
  }
  return match[2] === 'ms' ? amount : amount * 1000;
}

function parseRunexecBytes(value) {
  if (value == null || value === '') {
    return null;
  }
  const match = String(value).trim().match(/^(-?\d+)(B)?$/);
  if (!match) {
    return null;
  }
  const bytes = Number(match[1]);
  return Number.isFinite(bytes) ? bytes : null;
}

function parseRunexecMetrics(parsed = {}) {
  const normalized = parsed || {};
  return {
    walltimeMs: parseRunexecTimeToMs(normalized.walltime),
    cputimeMs: parseRunexecTimeToMs(normalized.cputime),
    memoryBytes: parseRunexecBytes(normalized.memory)
  };
}

function hasCompleteRunexecMetrics(parsed = {}) {
  const metrics = parseRunexecMetrics(parsed);
  return metrics.walltimeMs != null
    && metrics.cputimeMs != null
    && metrics.memoryBytes != null;
}

function runexecIndicatesFailure(parsed = {}) {
  const normalized = parsed || {};
  if (normalized.terminationReason) {
    return true;
  }
  return normalized.returnValue != null && normalized.returnValue !== 0;
}

function isInfraMetricsGap(parsedOutput, runexecParsed) {
  const returnValue = runexecParsed?.returnValue;
  return isSuccessfulStructuredOutput(parsedOutput)
    && (returnValue == null || returnValue === 0)
    && !hasCompleteRunexecMetrics(runexecParsed);
}

function computeRunexecTimeLimits(timeoutSeconds, coreBinding) {
  if (!Number.isFinite(timeoutSeconds) || timeoutSeconds <= 0) {
    return {
      timelimitSeconds: undefined,
      walltimelimitSeconds: undefined
    };
  }
  const coreCount = Array.isArray(coreBinding) && coreBinding.length > 0
    ? coreBinding.length
    : 0;
  return {
    timelimitSeconds: coreCount > 0 ? timeoutSeconds * coreCount : undefined,
    walltimelimitSeconds: timeoutSeconds
  };
}

function selectEffectiveTime(parsedOutput, runexecParsed) {
  const metrics = parseRunexecMetrics(runexecParsed);
  if (parsedOutput?.elapsed_ms != null) {
    return {
      time: parsedOutput.elapsed_ms,
      timeSource: 'tool',
      ...metrics
    };
  }
  if (metrics.walltimeMs != null) {
    return {
      time: metrics.walltimeMs,
      timeSource: 'runexec_walltime',
      ...metrics
    };
  }
  if (metrics.cputimeMs != null) {
    return {
      time: metrics.cputimeMs,
      timeSource: 'runexec_cputime',
      ...metrics
    };
  }
  return {
    time: null,
    timeSource: null,
    ...metrics
  };
}

function clampLog(data) {
  if (!data) {
    return '';
  }
  const text = String(data);
  if (text.length <= LOG_LIMIT) {
    return text;
  }
  return `${text.slice(0, LOG_LIMIT)}…`;
}

function encodeRegex(regex) {
  return Buffer.from(regex, 'utf8').toString('base64');
}

async function readOptionalText(filePath) {
  try {
    return await fs.readFile(filePath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
}

function normalizeTimeoutSeconds(timeoutMs) {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    return undefined;
  }
  return Math.max(1, Math.ceil(timeoutMs / 1000));
}

function inferErrorType({ explicitType, terminationReason, returnValue, stdout, stderr, programOutputTail, parsedOutput, missingOutput }) {
  if (explicitType) {
    return explicitType;
  }
  const text = `${stdout || ''}\n${stderr || ''}\n${programOutputTail || ''}\n${JSON.stringify(parsedOutput || {})}`;
  const lowered = text.toLowerCase();
  if (terminationReason && /cputime|walltime|timeout/.test(terminationReason)) {
    return 'timeout';
  }
  if (terminationReason && /memory|memlimit|outofmemory|oom/.test(terminationReason)) {
    return 'memory_limit';
  }
  if (returnValue != null && returnValue === 137 && lowered.includes('killed')) {
    return 'memory_limit';
  }
  if (returnValue != null && returnValue < 0) {
    return 'tool_exception';
  }
  if (TOOL_EXCEPTION_PATTERNS.some(pattern => text.includes(pattern))) {
    return 'tool_exception';
  }
  if (lowered.includes('timed out') || lowered.includes('timeout')) {
    return 'timeout';
  }
  if (lowered.includes('out of memory') || lowered.includes('oom') || lowered.includes('memlimit')) {
    return 'memory_limit';
  }
  if (missingOutput && (terminationReason === 'failed' || (returnValue != null && returnValue !== 0))) {
    return 'tool_exception';
  }
  if (missingOutput) {
    return 'output_missing';
  }
  if (returnValue != null && returnValue !== 0) {
    return 'child_exit_nonzero';
  }
  return 'tool_exception';
}

function normalizeStructuredError(parsedOutput) {
  if (!parsedOutput || typeof parsedOutput !== 'object' || Array.isArray(parsedOutput)) {
    return null;
  }
  const raw = parsedOutput.error;
  if (!raw) {
    return null;
  }
  if (typeof raw === 'string') {
    return {
      type: null,
      message: raw
    };
  }
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    return {
      ...raw,
      type: raw.type || null,
      message: raw.message || 'Tool execution failed'
    };
  }
  return {
    type: null,
    message: String(raw)
  };
}

function isSuccessfulStructuredOutput(parsedOutput) {
  return Boolean(
    parsedOutput
    && typeof parsedOutput === 'object'
    && !Array.isArray(parsedOutput)
    && !normalizeStructuredError(parsedOutput)
  );
}

function buildFailureDetails({
  cause,
  parsedOutput,
  stdout,
  stderr,
  rawOutput,
  durationMs,
  runexecParsed,
  missingOutput,
  runexecStdout,
  runexecStderr
}) {
  const effectiveTiming = selectEffectiveTime(parsedOutput, runexecParsed);
  const structuredError = normalizeStructuredError(parsedOutput);
  const message = structuredError?.message
    || cause?.message
    || 'Tool execution failed';
  const errorType = inferErrorType({
    explicitType: structuredError?.type,
    terminationReason: runexecParsed?.terminationReason,
    returnValue: runexecParsed?.returnValue,
    stdout,
    stderr,
    programOutputTail: stdout,
    parsedOutput,
    missingOutput
  });

  return {
    message,
    type: errorType,
    terminationReason: structuredError?.terminationReason || runexecParsed?.terminationReason || null,
    returnValue: structuredError?.returnValue ?? runexecParsed?.returnValue ?? null,
    stdout: clampLog(stdout),
    stderr: clampLog(stderr),
    runexecStdout: clampLog(runexecStdout),
    runexecStderr: clampLog(runexecStderr),
    programOutputTail: clampLog(stdout),
    durationMs,
    time: effectiveTiming.time,
    timeSource: effectiveTiming.timeSource,
    walltimeMs: effectiveTiming.walltimeMs,
    cputimeMs: effectiveTiming.cputimeMs,
    memoryBytes: effectiveTiming.memoryBytes,
    rawOutput,
    parsedOutput,
    logs: [
      ...stdout ? [{ stream: 'stdout', content: clampLog(stdout) }] : [],
      ...stderr ? [{ stream: 'stderr', content: clampLog(stderr) }] : []
    ]
  };
}

function buildInfraError({
  parsedOutput,
  stdout,
  stderr,
  rawOutput,
  durationMs,
  runexecParsed,
  runexecStdout,
  runexecStderr,
  attempt,
  maxAttempts
}) {
  const details = buildFailureDetails({
    cause: new Error('runexec did not provide complete metrics for successful tool execution.'),
    parsedOutput,
    stdout,
    stderr,
    rawOutput,
    durationMs,
    runexecParsed,
    missingOutput: !rawOutput,
    runexecStdout,
    runexecStderr
  });
  return Object.assign(new Error(details.message), {
    ...details,
    type: 'infra_error',
    inconclusive: true,
    retryable: true,
    attempt,
    maxAttempts
  });
}

function prepResult(jobManager, job, toolId, statusUpdates = {}) {
  return jobManager.updateResult(job, toolId, result => {
    Object.assign(result, statusUpdates);
  });
}

async function executeToolAttempt(
  toolId,
  regexBase64,
  timeoutMs,
  { cpuAllocator, cpuCores, memoryMB, toolOptions, cores, attempt = 1, maxAttempts = MAX_INFRA_RETRIES } = {}
) {
  const definition = TOOL_DEFINITIONS[toolId];
  if (!definition) {
    throw new Error(`Unknown tool: ${toolId}`);
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `redos-tool-${toolId}-`));
  const outputPath = path.join(tempDir, 'output.json');
  const programOutputPath = path.join(tempDir, 'output.log');

  const { file, args, options = {} } = definition.buildCommand(regexBase64, outputPath, toolOptions);
  const start = Date.now();
  let stdout = '';
  let stderr = '';
  let parsedOutput = null;
  let rawOutput = null;
  let runexecParsed = null;
  let runexecStdout = '';
  let runexecStderr = '';
  let effectiveTiming = null;
  let allocated = null;
  const explicitCores = Array.isArray(cores)
    ? cores.filter(value => Number.isInteger(value) && value >= 0)
    : null;
  let coreBinding = explicitCores && explicitCores.length > 0 ? explicitCores : null;
  const timeoutSeconds = normalizeTimeoutSeconds(timeoutMs);
  const runexecTimeoutSeconds = timeoutSeconds ? timeoutSeconds + TOOL_TIMEOUT_GRACE_SECONDS : undefined;

  try {
    if (!coreBinding && cpuAllocator && Number.isFinite(cpuCores) && cpuCores > 0) {
      allocated = await cpuAllocator.acquire(cpuCores);
      coreBinding = allocated.cores;
    }

    const env = {
      ...(options.env || {})
    };
    if (timeoutSeconds) {
      env.TOOL_TIMEOUT_SECONDS = String(timeoutSeconds);
      if (toolId === 'regexstatic') {
        env.REGEXSTATIC_TIMEOUT_SECONDS = String(timeoutSeconds);
      }
      if (toolId === 'grewia') {
        env.GREWIA_TIMEOUT_SECONDS = String(timeoutSeconds);
      }
    }

    const runexecLimits = computeRunexecTimeLimits(runexecTimeoutSeconds, coreBinding);

    const runexecResult = await runWithRunexec({
      cmd: file,
      args,
      cwd: options.cwd,
      env,
      outputLogPath: programOutputPath,
      timelimitSeconds: runexecLimits.timelimitSeconds,
      walltimelimitSeconds: runexecLimits.walltimelimitSeconds,
      memoryMB,
      cores: coreBinding
    });
    runexecParsed = runexecResult.parsed;
    runexecStdout = runexecResult.stdout || '';
    runexecStderr = runexecResult.stderr || '';
    stdout = (await readOptionalText(programOutputPath)) || '';
    stderr = '';

    rawOutput = await fs.readFile(outputPath, 'utf8');
    parsedOutput = JSON.parse(rawOutput);
    effectiveTiming = selectEffectiveTime(parsedOutput, runexecParsed);
    const structuredError = normalizeStructuredError(parsedOutput);
    if (structuredError) {
      const details = buildFailureDetails({
        parsedOutput,
        stdout,
        stderr,
        rawOutput,
        durationMs: Date.now() - start,
        runexecParsed,
        runexecStdout,
        runexecStderr
      });
      throw Object.assign(new Error(details.message), {
        ...details,
        cause: structuredError
      });
    }
    if (isInfraMetricsGap(parsedOutput, runexecParsed)) {
      throw buildInfraError({
        parsedOutput,
        stdout,
        stderr,
        rawOutput,
        durationMs: Date.now() - start,
        runexecParsed,
        runexecStdout,
        runexecStderr,
        attempt,
        maxAttempts
      });
    }
  } catch (error) {
    stdout = (await readOptionalText(programOutputPath)) || error.stdout || stdout;
    if (error.stderr) {
      stderr = error.stderr;
    }
    if (error.parsed) {
      runexecParsed = error.parsed;
    }
    if (error.stdout) {
      runexecStdout = error.stdout;
    }
    if (error.stderr) {
      runexecStderr = error.stderr;
    }
    try {
      const maybeRaw = await fs.readFile(outputPath, 'utf8');
      rawOutput = maybeRaw;
      parsedOutput = JSON.parse(maybeRaw);
    } catch {
      // ignore read/parse errors
    }
    if (isSuccessfulStructuredOutput(parsedOutput)
        && !runexecIndicatesFailure(runexecParsed)
        && hasCompleteRunexecMetrics(runexecParsed)) {
      effectiveTiming = selectEffectiveTime(parsedOutput, runexecParsed);
      return {
        stdout,
        stderr,
        parsedOutput,
        rawOutput,
        runexecParsed,
        effectiveTiming,
        durationMs: Date.now() - start
      };
    }
    if (isInfraMetricsGap(parsedOutput, runexecParsed)) {
      throw buildInfraError({
        parsedOutput,
        stdout,
        stderr,
        rawOutput,
        durationMs: Date.now() - start,
        runexecParsed,
        runexecStdout,
        runexecStderr,
        attempt,
        maxAttempts
      });
    }
    const details = buildFailureDetails({
      cause: error,
      parsedOutput,
      stdout,
      stderr,
      rawOutput,
      durationMs: Date.now() - start,
      runexecParsed,
      missingOutput: !rawOutput,
      runexecStdout,
      runexecStderr
    });
    throw Object.assign(new Error(details.message), {
      ...details,
      cause: error
    });
  } finally {
    try { allocated?.release(); } catch {}
    await fs.rm(tempDir, { recursive: true, force: true });
  }

  return {
    stdout,
    stderr,
    parsedOutput,
    rawOutput,
    runexecParsed,
    effectiveTiming,
    durationMs: Date.now() - start
  };
}

async function executeTool(toolId, regexBase64, timeoutMs, options = {}) {
  let lastError;
  for (let attempt = 1; attempt <= MAX_INFRA_RETRIES; attempt += 1) {
    try {
      return await executeToolAttempt(toolId, regexBase64, timeoutMs, {
        ...options,
        attempt,
        maxAttempts: MAX_INFRA_RETRIES
      });
    } catch (error) {
      lastError = error;
      if (!(error?.retryable && error?.type === 'infra_error' && attempt < MAX_INFRA_RETRIES)) {
        throw error;
      }
    }
  }
  throw lastError;
}

async function runToolsJob(jobManager, job, { regex, toolIds, toolOptions = {}, timeoutMs, cpuAllocator, cpuCores, memoryMB }) {
  const effectiveTimeout = timeoutMs || undefined;
  const regexBase64 = encodeRegex(regex);

  jobManager.updateJob(job, { status: 'running' });

  const executions = toolIds.map(toolId => (async () => {
    const definition = TOOL_DEFINITIONS[toolId];
    if (!definition) {
      prepResult(jobManager, job, toolId, {
        status: 'failed',
        error: {
          message: `Unsupported tool: ${toolId}`
        },
        finishedAt: new Date().toISOString()
      });
      jobManager.incrementProgress(job);
      return;
    }

    prepResult(jobManager, job, toolId, {
      status: 'running',
      startedAt: new Date().toISOString()
    });

    try {
      const result = await executeTool(toolId, regexBase64, effectiveTimeout, {
        cpuAllocator,
        cpuCores,
        memoryMB,
        toolOptions: toolOptions[toolId]
      });
      const effectiveTiming = result.effectiveTiming || selectEffectiveTime(result.parsedOutput, result.runexecParsed);
      const normalizedOutput = {
        ...(result.parsedOutput || {}),
        time: effectiveTiming.time,
        time_source: effectiveTiming.timeSource,
        walltime_ms: effectiveTiming.walltimeMs,
        cputime_ms: effectiveTiming.cputimeMs,
        memory_bytes: effectiveTiming.memoryBytes
      };

      prepResult(jobManager, job, toolId, {
        status: 'completed',
        finishedAt: new Date().toISOString(),
        elapsedMs: effectiveTiming.time ?? result.durationMs,
        output: normalizedOutput,
        rawOutput: result.rawOutput,
        logs: [
          ...result.stdout ? [{ stream: 'stdout', content: clampLog(result.stdout) }] : [],
          ...result.stderr ? [{ stream: 'stderr', content: clampLog(result.stderr) }] : []
        ]
      });
    } catch (error) {
      prepResult(jobManager, job, toolId, {
        status: error.inconclusive ? 'inconclusive' : 'failed',
        finishedAt: new Date().toISOString(),
        elapsedMs: error.time ?? (error.durationMs || null),
        error: {
          message: error.message,
          type: error.type || null,
          terminationReason: error.terminationReason || null,
          returnValue: error.returnValue ?? null,
          time: error.time ?? null,
          timeSource: error.timeSource || null,
          walltimeMs: error.walltimeMs ?? null,
          cputimeMs: error.cputimeMs ?? null,
          memoryBytes: error.memoryBytes ?? null,
          stdout: clampLog(error.stdout),
          stderr: clampLog(error.stderr),
          runexecStdout: error.runexecStdout || '',
          runexecStderr: error.runexecStderr || '',
          programOutputTail: error.programOutputTail || clampLog(error.stdout)
        },
        rawOutput: error.rawOutput,
        output: error.parsedOutput || undefined,
        logs: error.logs || [
          ...error.stdout ? [{ stream: 'stdout', content: clampLog(error.stdout) }] : [],
          ...error.stderr ? [{ stream: 'stderr', content: clampLog(error.stderr) }] : []
        ]
      });
    } finally {
      jobManager.incrementProgress(job);
    }
  })());

  await Promise.allSettled(executions);

  const hasNonCompleted = job.results.some(result => result.status !== 'completed');
  const finalStatus = hasNonCompleted ? 'completed_with_errors' : 'completed';
  jobManager.finalizeJob(job, finalStatus);
}

module.exports = {
  runToolsJob,
  executeTool,
  clampLog,
  encodeRegex,
  parseRunexecMetrics,
  hasCompleteRunexecMetrics,
  selectEffectiveTime,
  normalizeStructuredError,
  inferErrorType,
  isSuccessfulStructuredOutput,
  runexecIndicatesFailure,
  computeRunexecTimeLimits
};
