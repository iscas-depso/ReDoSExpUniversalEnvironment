const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const util = require('util');
const childProcess = require('child_process');

const execFile = util.promisify(childProcess.execFile);

const { ENGINE_DEFINITIONS, DEFAULT_OPTIONS } = require('./definitions');
const { runWithRunexec } = require('./runexec');

const LOG_LIMIT = 4000;

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
  const desiredRepeat = override > 0 ? override : recommendedRepeat;

  const maxRepeatTimes = Math.max(1, options.maxRepeatTimes || DEFAULT_OPTIONS.maxRepeatTimes);
  const maxAttackLength = Math.max(64, options.maxAttackLength || DEFAULT_OPTIONS.maxAttackLength);

  let appliedRepeat = Math.min(Math.max(desiredRepeat, infix ? 1 : 0), maxRepeatTimes);

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
    appliedRepeat,
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

function prepResult(jobManager, job, engineId, statusUpdates = {}) {
  return jobManager.updateResult(job, engineId, result => {
    Object.assign(result, statusUpdates);
  });
}

async function executeEngine(engineId, payloadPath, regexBase64, matchMode, timeoutMs, { cpuAllocator, cpuCores, memoryMB } = {}) {
  const definition = ENGINE_DEFINITIONS[engineId];
  if (!definition) {
    throw new Error(`Unknown engine: ${engineId}`);
  }

  const { binaryPath } = definition;
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `redos-engine-${engineId}-`));
  const programOutputPath = path.join(tempDir, 'output.log');
  let allocated = null;
  let runexecFallbackLogs = [];
  const useRunexec = process.env.DISABLE_RUNEXEC !== '1';
  try {
    if (cpuAllocator && Number.isFinite(cpuCores) && cpuCores > 0) {
      allocated = await cpuAllocator.acquire(cpuCores);
    }
    if (useRunexec) {
      try {
        await runWithRunexec({
          cmd: binaryPath,
          args: [regexBase64, payloadPath, String(matchMode)],
          cwd: path.dirname(binaryPath),
          env: {
            PATH: `${process.env.PATH || ''}:/usr/local/bin:/home/developer/.nvm/versions/node/v21.7.3/bin:/home/developer/.nvm/versions/node/v14.21.3/bin`
          },
          outputLogPath: programOutputPath,
          timelimitSeconds: timeoutMs ? Math.floor(timeoutMs / 1000) : undefined,
          walltimelimitSeconds: timeoutMs ? Math.floor(timeoutMs / 1000) : undefined,
          memoryMB,
          cores: allocated?.cores
        });
        let stdout = '';
        try { stdout = await fs.readFile(programOutputPath, 'utf8'); } catch {}
        const stderr = '';
        return { stdout, stderr, runexecFallbackLogs };
      } catch (error) {
        if (error.code !== 'RUNEXEC_UNAVAILABLE') {
          throw error;
        }
        runexecFallbackLogs = [
          ...error.stdout ? [{ stream: 'stderr', content: clampLog(error.stdout) }] : [],
          ...error.stderr ? [{ stream: 'stderr', content: clampLog(error.stderr) }] : []
        ];
      }
    } else {
      const execOptions = {
        cwd: path.dirname(binaryPath),
        env: {
          ...process.env,
          PATH: `${process.env.PATH || ''}:/usr/local/bin:/home/developer/.nvm/versions/node/v21.7.3/bin:/home/developer/.nvm/versions/node/v14.21.3/bin`
        },
        timeout: timeoutMs,
        maxBuffer: 20 * 1024 * 1024
      };
      const result = await execFile(binaryPath, [regexBase64, payloadPath, String(matchMode)], execOptions);
      return { stdout: result.stdout || '', stderr: result.stderr || '', runexecFallbackLogs };
    }

    const execOptions = {
      cwd: path.dirname(binaryPath),
      env: {
        ...process.env,
        PATH: `${process.env.PATH || ''}:/usr/local/bin:/home/developer/.nvm/versions/node/v21.7.3/bin:/home/developer/.nvm/versions/node/v14.21.3/bin`
      },
      timeout: timeoutMs,
      maxBuffer: 20 * 1024 * 1024
    };
    const result = await execFile(binaryPath, [regexBase64, payloadPath, String(matchMode)], execOptions);
    return { stdout: result.stdout || '', stderr: result.stderr || '', runexecFallbackLogs };
  } finally {
    try { allocated?.release(); } catch {}
    await fs.rm(tempDir, { recursive: true, force: true });
  }
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
      const start = Date.now();
      const result = await executeEngine(
        engineId,
        payloadPath,
        regexBase64,
        matchMode,
        effectiveTimeout,
        { cpuAllocator, cpuCores, memoryMB }
      );
      const parsed = parseEngineOutput(result.stdout);

      prepResult(jobManager, job, engineId, {
        status: 'completed',
        finishedAt: new Date().toISOString(),
        elapsedMs: parsed?.elapsedMs ?? Date.now() - start,
        output: {
          elapsed_ms: parsed?.elapsedMs ?? null,
          match_count: parsed?.matchCount ?? null,
          raw: result.stdout?.trim() || ''
        },
        logs: [
          ...result.runexecFallbackLogs,
          ...result.stdout ? [{ stream: 'stdout', content: clampLog(result.stdout) }] : [],
          ...result.stderr ? [{ stream: 'stderr', content: clampLog(result.stderr) }] : []
        ]
      });
    } catch (error) {
      prepResult(jobManager, job, engineId, {
        status: 'failed',
        finishedAt: new Date().toISOString(),
        error: {
          message: error.message,
          stdout: clampLog(error.stdout),
          stderr: clampLog(error.stderr)
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

  const hasFailure = job.results.some(result => result.status === 'failed');
  const finalStatus = hasFailure ? 'completed_with_errors' : 'completed';
  jobManager.finalizeJob(job, finalStatus);
}

module.exports = {
  runEnginesJob,
  buildAttackPayload
};
