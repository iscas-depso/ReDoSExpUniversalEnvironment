const fs = require('fs/promises');
const os = require('os');
const path = require('path');

const { ENGINE_DEFINITIONS, DEFAULT_OPTIONS } = require('./definitions');
const { runWithRunexec } = require('./runexec');

const LOG_LIMIT = 4000;
const MAX_INFRA_RETRIES = 3;
const ENGINE_EXCEPTION_PATTERNS = [
  'StackOverflowError',
  'Exception in thread',
  'Traceback (most recent call last):',
  'Unhandled exception',
  'Segmentation fault',
  'core dumped'
];

function clampLog(data) {
  if (!data) {
    return '';
  }
  const text = String(data);
  if (text.length <= LOG_LIMIT) {
    return text;
  }
  // Use ASCII ellipsis to avoid encoding issues inside containers
  return `${text.slice(0, LOG_LIMIT)}...`;
}

function encodeRegex(regex) {
  return Buffer.from(regex, 'utf8').toString('base64');
}

function decodeBase64(value) {
  if (!value) {
    return '';
  }
  try {
    return Buffer.from(value, 'base64').toString('utf8');
  } catch {
    return '';
  }
}

function parseRepeat(value) {
  const num = Number(value);
  if (!Number.isFinite(num) || num < 0) {
    return 0;
  }
  return num;
}

function buildAttackPayload(attack, options) {
  if (attack?.fullText) {
    const attackText = decodeBase64(attack.fullText);
    const maxAttackLength = Math.max(64, options.maxAttackLength || DEFAULT_OPTIONS.maxAttackLength);
    const truncated = attackText.length > maxAttackLength;
    const finalText = truncated ? attackText.slice(0, maxAttackLength) : attackText;
    return {
      attackText: finalText,
      payloadInfo: {
        mode: 'fullText',
        originalLength: attackText.length,
        truncated,
        payloadLength: finalText.length
      }
    };
  }

  const prefix = decodeBase64(attack?.prefix);
  const infix = decodeBase64(attack?.infix);
  const suffix = decodeBase64(attack?.suffix);

  const recommendedRepeat = parseRepeat(
    attack?.repeat_times ?? attack?.repeatTimes ?? attack?.repeat
  );

  const override = parseRepeat(options.repeatOverride);
  const maxRepeatTimes = Math.max(1, options.maxRepeatTimes || DEFAULT_OPTIONS.maxRepeatTimes);
  const maxAttackLength = Math.max(64, options.maxAttackLength || DEFAULT_OPTIONS.maxAttackLength);
  const fixedLength = prefix.length + suffix.length;
  const maxRepeatByLength = infix.length > 0
    ? Math.max(0, Math.floor((maxAttackLength - fixedLength) / infix.length))
    : 0;
  const repeatBudget = Math.min(maxRepeatTimes, maxRepeatByLength);
  let appliedRepeat = override > 0
    ? Math.min(override, repeatBudget)
    : repeatBudget;

  let attackText = prefix;
  let truncated = false;

  const appendChunk = chunk => {
    if (!chunk) {
      return;
    }
    if (attackText.length + chunk.length > maxAttackLength) {
      const remaining = maxAttackLength - attackText.length;
      if (remaining > 0) {
        attackText += chunk.slice(0, remaining);
        truncated = true;
      } else {
        truncated = true;
      }
    } else {
      attackText += chunk;
    }
  };

  for (let i = 0; i < appliedRepeat; i += 1) {
    appendChunk(infix);
    if (truncated) {
      appliedRepeat = i + 1;
      break;
    }
  }

  appendChunk(suffix);

  if (!attackText.length) {
    attackText = prefix || infix || suffix || '';
  }

  const payloadInfo = {
    prefixLength: prefix.length,
    infixLength: infix.length,
    suffixLength: suffix.length,
    recommendedRepeat,
    appliedRepeat,
    maxRepeatByLength,
    truncated,
    payloadLength: attackText.length
  };

  return { attackText, payloadInfo };
}

function parseEngineOutput(stdout) {
  if (!stdout) {
    return null;
  }

  const trimmed = stdout.trim();
  const match = trimmed.match(/(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+)/);
  if (!match) {
    return null;
  }

  return {
    elapsedMs: Number(match[1]),
    matchCount: Number(match[2])
  };
}

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
  if (parsedOutput?.elapsedMs != null) {
    return {
      time: parsedOutput.elapsedMs,
      timeSource: 'engine',
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

function hasFatalEngineOutput(text) {
  return ENGINE_EXCEPTION_PATTERNS.some(pattern => String(text || '').includes(pattern));
}

function inferEngineFailureType({ runexecParsed, stdout, stderr, parsedOutput }) {
  const text = `${stdout || ''}\n${stderr || ''}`;
  const terminationReason = runexecParsed?.terminationReason || null;
  const returnValue = runexecParsed?.returnValue;

  if (terminationReason && /walltime|cputime|timeout/.test(terminationReason)) {
    return 'timeout';
  }
  if (terminationReason && /memory|memlimit|outofmemory|oom/.test(terminationReason)) {
    return 'memory_limit';
  }
  if (ENGINE_EXCEPTION_PATTERNS.some(pattern => text.includes(pattern))) {
    return 'tool_exception';
  }
  if (returnValue != null && returnValue !== 0) {
    return 'child_exit_nonzero';
  }
  if (!parsedOutput) {
    return 'invalid_output';
  }
  return 'tool_exception';
}

function buildEngineExecutionError(message, { runexecParsed, stdout, stderr, parsedOutput, runexecStdout, runexecStderr } = {}) {
  const effectiveTiming = selectEffectiveTime(parsedOutput, runexecParsed);
  const error = new Error(message);
  error.type = inferEngineFailureType({ runexecParsed, stdout, stderr, parsedOutput });
  error.terminationReason = runexecParsed?.terminationReason || null;
  error.returnValue = runexecParsed?.returnValue ?? null;
  error.stdout = stdout || '';
  error.stderr = stderr || '';
  error.runexecStdout = runexecStdout || '';
  error.runexecStderr = runexecStderr || '';
  error.parsedOutput = parsedOutput || null;
  error.time = effectiveTiming.time;
  error.timeSource = effectiveTiming.timeSource;
  error.walltimeMs = effectiveTiming.walltimeMs;
  error.cputimeMs = effectiveTiming.cputimeMs;
  error.memoryBytes = effectiveTiming.memoryBytes;
  return error;
}

function buildEngineInfraError({
  engineId,
  runexecParsed,
  stdout,
  stderr,
  parsedOutput,
  runexecStdout,
  runexecStderr,
  attempt,
  maxAttempts
}) {
  const error = buildEngineExecutionError(
    `runexec did not provide complete metrics for successful engine execution (${engineId}).`,
    { runexecParsed, stdout, stderr, parsedOutput, runexecStdout, runexecStderr }
  );
  error.type = 'infra_error';
  error.inconclusive = true;
  error.retryable = true;
  error.attempt = attempt;
  error.maxAttempts = maxAttempts;
  return error;
}

function prepResult(jobManager, job, engineId, statusUpdates = {}) {
  return jobManager.updateResult(job, engineId, result => {
    Object.assign(result, statusUpdates);
  });
}

async function executeEngineAttempt(
  engineId,
  payloadPath,
  regexBase64,
  matchMode,
  timeoutMs,
  { cpuAllocator, cpuCores, memoryMB, cores, attempt = 1, maxAttempts = MAX_INFRA_RETRIES } = {}
) {
  const definition = ENGINE_DEFINITIONS[engineId];
  if (!definition) {
    throw new Error(`Unknown engine: ${engineId}`);
  }

  const { binaryPath } = definition;
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `redos-engine-${engineId}-`));
  const programOutputPath = path.join(tempDir, 'output.log');
  let allocated = null;
  const explicitCores = Array.isArray(cores)
    ? cores.filter(value => Number.isInteger(value) && value >= 0)
    : null;
  let coreBinding = explicitCores && explicitCores.length > 0 ? explicitCores : null;
  try {
    if (!coreBinding && cpuAllocator && Number.isFinite(cpuCores) && cpuCores > 0) {
      allocated = await cpuAllocator.acquire(cpuCores);
      coreBinding = allocated.cores;
    }
    const timeoutSeconds = timeoutMs ? Math.floor(timeoutMs / 1000) : undefined;
    const runexecLimits = computeRunexecTimeLimits(timeoutSeconds, coreBinding);
    const runexecResult = await runWithRunexec({
      cmd: binaryPath,
      args: [regexBase64, payloadPath, String(matchMode)],
      cwd: path.dirname(binaryPath),
      env: {
        PATH: `${process.env.PATH || ''}:/usr/local/bin:/home/developer/.nvm/versions/node/v21.7.3/bin:/home/developer/.nvm/versions/node/v14.21.3/bin`
      },
      outputLogPath: programOutputPath,
      timelimitSeconds: runexecLimits.timelimitSeconds,
      walltimelimitSeconds: runexecLimits.walltimelimitSeconds,
      memoryMB,
      cores: coreBinding
    });
    let stdout = '';
    try { stdout = await fs.readFile(programOutputPath, 'utf8'); } catch {}
    const stderr = runexecResult.stderr || '';
    const parsedOutput = parseEngineOutput(stdout);
    const effectiveTiming = selectEffectiveTime(parsedOutput, runexecResult.parsed);

    if (runexecResult.parsed?.terminationReason) {
      throw buildEngineExecutionError(
        `Engine ${engineId} exceeded execution limits (${runexecResult.parsed.terminationReason}).`,
        {
          runexecParsed: runexecResult.parsed,
          stdout,
          stderr,
          parsedOutput,
          runexecStdout: runexecResult.stdout || '',
          runexecStderr: runexecResult.stderr || ''
        }
      );
    }

    if (runexecResult.parsed?.returnValue != null && runexecResult.parsed.returnValue !== 0) {
      throw buildEngineExecutionError(
        `Engine ${engineId} exited with code ${runexecResult.parsed.returnValue}.`,
        {
          runexecParsed: runexecResult.parsed,
          stdout,
          stderr,
          parsedOutput,
          runexecStdout: runexecResult.stdout || '',
          runexecStderr: runexecResult.stderr || ''
        }
      );
    }

    if (hasFatalEngineOutput(stdout) || hasFatalEngineOutput(stderr)) {
      throw buildEngineExecutionError(
        `Engine ${engineId} reported a fatal exception during verification.`,
        {
          runexecParsed: runexecResult.parsed,
          stdout,
          stderr,
          parsedOutput,
          runexecStdout: runexecResult.stdout || '',
          runexecStderr: runexecResult.stderr || ''
        }
      );
    }

    if (parsedOutput && !hasCompleteRunexecMetrics(runexecResult.parsed)) {
      throw buildEngineInfraError({
        engineId,
        runexecParsed: runexecResult.parsed,
        stdout,
        stderr,
        parsedOutput,
        runexecStdout: runexecResult.stdout || '',
        runexecStderr: runexecResult.stderr || '',
        attempt,
        maxAttempts
      });
    }

    return {
      stdout,
      stderr,
      parsedOutput,
      runexecParsed: runexecResult.parsed,
      effectiveTiming
    };
  } finally {
    try { allocated?.release(); } catch {}
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

async function executeEngine(engineId, payloadPath, regexBase64, matchMode, timeoutMs, options = {}) {
  let lastError;
  for (let attempt = 1; attempt <= MAX_INFRA_RETRIES; attempt += 1) {
    try {
      return await executeEngineAttempt(
        engineId,
        payloadPath,
        regexBase64,
        matchMode,
        timeoutMs,
        {
          ...options,
          attempt,
          maxAttempts: MAX_INFRA_RETRIES
        }
      );
    } catch (error) {
      lastError = error;
      if (!(error?.retryable && error?.type === 'infra_error' && attempt < MAX_INFRA_RETRIES)) {
        throw error;
      }
    }
  }
  throw lastError;
}

async function runEnginesJob(
  jobManager,
  job,
  {
    regex,
    engines,
    attack,
    matchMode = 0,
    timeoutMs,
    cpuAllocator,
    cpuCores,
    memoryMB,
    repeatOverride,
    maxAttackLength,
    maxRepeatTimes
  }
) {
  if (!attack) {
    jobManager.finalizeJob(job, 'failed', new Error('Attack components are required for engine verification.'));
    return;
  }

  const effectiveTimeout = timeoutMs || undefined;
  const options = {
    repeatOverride,
    maxRepeatTimes: maxRepeatTimes || DEFAULT_OPTIONS.maxRepeatTimes,
    maxAttackLength: maxAttackLength || DEFAULT_OPTIONS.maxAttackLength
  };

  const { attackText, payloadInfo } = buildAttackPayload(attack, options);

  if (!attackText || !attackText.length) {
    jobManager.finalizeJob(job, 'failed', new Error('Generated attack string is empty.'));
    return;
  }

  const regexBase64 = encodeRegex(regex);

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'redos-engine-'));
  const payloadPath = path.join(tempDir, 'payload.txt');
  await fs.writeFile(payloadPath, attackText, 'utf8');

  job.metadata = {
    ...job.metadata,
    payloadInfo,
    payloadPreview: attackText.slice(0, 256)
  };
  jobManager.updateJob(job, { status: 'running' });

  const executions = engines.map(engineId => (async () => {
    const definition = ENGINE_DEFINITIONS[engineId];
    if (!definition) {
      prepResult(jobManager, job, engineId, {
        status: 'failed',
        error: { message: `Unsupported engine: ${engineId}` },
        finishedAt: new Date().toISOString()
      });
      jobManager.incrementProgress(job);
      return;
    }

    prepResult(jobManager, job, engineId, {
      status: 'running',
      startedAt: new Date().toISOString()
    });

    try {
      const result = await executeEngine(
        engineId,
        payloadPath,
        regexBase64,
        matchMode,
        effectiveTimeout,
        { cpuAllocator, cpuCores, memoryMB }
      );
      const parsed = result.parsedOutput;
      const effectiveTiming = result.effectiveTiming || selectEffectiveTime(parsed, result.runexecParsed);

      prepResult(jobManager, job, engineId, {
        status: 'completed',
        finishedAt: new Date().toISOString(),
        elapsedMs: effectiveTiming.time,
        output: {
          elapsed_ms: parsed?.elapsedMs ?? null,
          match_count: parsed?.matchCount ?? null,
          time: effectiveTiming.time,
          time_source: effectiveTiming.timeSource,
          walltime_ms: effectiveTiming.walltimeMs,
          cputime_ms: effectiveTiming.cputimeMs,
          memory_bytes: effectiveTiming.memoryBytes,
          raw: result.stdout?.trim() || ''
        },
        logs: [
          ...result.stdout ? [{ stream: 'stdout', content: clampLog(result.stdout) }] : [],
          ...result.stderr ? [{ stream: 'stderr', content: clampLog(result.stderr) }] : []
        ]
      });
    } catch (error) {
      prepResult(jobManager, job, engineId, {
        status: error.inconclusive ? 'inconclusive' : 'failed',
        finishedAt: new Date().toISOString(),
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
          runexecStderr: error.runexecStderr || ''
        },
        logs: [
          ...error.stdout ? [{ stream: 'stdout', content: clampLog(error.stdout) }] : [],
          ...error.stderr ? [{ stream: 'stderr', content: clampLog(error.stderr) }] : []
        ]
      });
    } finally {
      jobManager.incrementProgress(job);
    }
  })());

  await Promise.allSettled(executions);
  await fs.rm(tempDir, { recursive: true, force: true });

  const hasNonCompleted = job.results.some(result => result.status !== 'completed');
  const finalStatus = hasNonCompleted ? 'completed_with_errors' : 'completed';
  jobManager.finalizeJob(job, finalStatus);
}

module.exports = {
  runEnginesJob,
  buildAttackPayload,
  executeEngine,
  parseEngineOutput,
  parseRunexecMetrics,
  selectEffectiveTime,
  buildEngineExecutionError,
  clampLog,
  encodeRegex
};
