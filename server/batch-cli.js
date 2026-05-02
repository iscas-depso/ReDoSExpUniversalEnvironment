const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const { detectVisibleCpuIds } = require('./cpu-allocator');

const {
  TOOL_DEFINITIONS,
  TOOL_METADATA,
  ENGINE_DEFINITIONS,
  ENGINE_METADATA,
  MATCH_MODES,
  DEFAULT_OPTIONS,
  normalizeToolOptions
} = require('./definitions');
const {
  executeTool,
  clampLog: clampToolLog,
  encodeRegex: encodeToolRegex,
  selectEffectiveTime: selectToolEffectiveTime
} = require('./tool-runner');
const {
  buildAttackPayload,
  executeEngine,
  parseEngineOutput,
  selectEffectiveTime,
  clampLog: clampEngineLog,
  encodeRegex: encodeEngineRegex
} = require('./engine-runner');

function normalizeTimeoutMs(timeoutSeconds, defaultTimeoutMs) {
  const timeoutNum = Number(timeoutSeconds);
  if (!Number.isFinite(timeoutNum) || timeoutNum <= 0) {
    return undefined;
  }
  return Math.min(timeoutNum, 3600) * 1000 || defaultTimeoutMs;
}

function normalizePositiveNumber(value) {
  const num = Number(value);
  if (!Number.isFinite(num) || num <= 0) {
    return undefined;
  }
  return num;
}

function normalizeCoreList(value) {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const cores = [...new Set(
    value
      .map(item => Number(item))
      .filter(item => Number.isInteger(item) && item >= 0)
  )].sort((a, b) => a - b);
  return cores.length > 0 ? cores : undefined;
}

function hasCompleteTiming(output = {}) {
  return output.walltime_ms != null
    && output.cputime_ms != null
    && output.memory_bytes != null;
}

function buildToolInfraResult({ toolId, result, effectiveTiming, normalizedToolOptions }) {
  return {
    status: 'inconclusive',
    toolId,
    elapsedMs: effectiveTiming.time ?? result.durationMs ?? null,
    output: {
      ...(result.parsedOutput || {}),
      time: effectiveTiming.time,
      time_source: effectiveTiming.timeSource,
      walltime_ms: effectiveTiming.walltimeMs,
      cputime_ms: effectiveTiming.cputimeMs,
      memory_bytes: effectiveTiming.memoryBytes
    },
    rawOutput: result.rawOutput,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    logs: [
      ...result.stdout ? [{ stream: 'stdout', content: clampToolLog(result.stdout) }] : [],
      ...result.stderr ? [{ stream: 'stderr', content: clampToolLog(result.stderr) }] : []
    ],
    error: {
      message: 'runexec did not provide complete metrics for successful tool execution.',
      type: 'infra_error',
      terminationReason: result.runexecParsed?.terminationReason || null,
      returnValue: result.runexecParsed?.returnValue ?? null,
      time: effectiveTiming.time ?? null,
      timeSource: effectiveTiming.timeSource || null,
      walltimeMs: effectiveTiming.walltimeMs ?? null,
      cputimeMs: effectiveTiming.cputimeMs ?? null,
      memoryBytes: effectiveTiming.memoryBytes ?? null,
      stdout: clampToolLog(result.stdout),
      stderr: clampToolLog(result.stderr),
      runexecStdout: '',
      runexecStderr: '',
      programOutputTail: clampToolLog(result.stdout)
    },
    normalizedToolOptions
  };
}

function getBatchMeta() {
  const visibleCpuIds = detectVisibleCpuIds();
  return {
    tools: TOOL_METADATA,
    engines: ENGINE_METADATA,
    matchModes: MATCH_MODES,
    defaults: {
      toolTimeoutSeconds: Math.round(DEFAULT_OPTIONS.toolTimeoutMs / 1000),
      engineTimeoutSeconds: Math.round(DEFAULT_OPTIONS.engineTimeoutMs / 1000),
      maxRepeatTimes: DEFAULT_OPTIONS.maxRepeatTimes,
      maxAttackLength: DEFAULT_OPTIONS.maxAttackLength,
      defaultCores: DEFAULT_OPTIONS.defaultCores || null,
      defaultMemoryMB: DEFAULT_OPTIONS.defaultMemoryMB || null
    },
    runtime: {
      visibleCpuIds,
      visibleCpuCount: visibleCpuIds.length
    }
  };
}

async function runToolBatch(payload = {}) {
  const regex = typeof payload.regex === 'string' ? payload.regex.trim() : '';
  const toolId = String(payload.toolId || '').trim();

  if (!regex) {
    throw new Error('regex is required.');
  }
  if (!TOOL_DEFINITIONS[toolId]) {
    throw new Error(`Unsupported tool: ${toolId}`);
  }

  const normalizedToolOptions = normalizeToolOptions(toolId, payload.toolOptions);
  const timeoutMs = normalizeTimeoutMs(payload.timeoutSeconds, DEFAULT_OPTIONS.toolTimeoutMs);
  const cpuCores = normalizePositiveNumber(payload.cpuCores);
  const memoryMB = normalizePositiveNumber(payload.memoryMB);
  const cores = normalizeCoreList(payload.cores);

  try {
    const result = await executeTool(toolId, encodeToolRegex(regex), timeoutMs, {
      cpuCores,
      memoryMB,
      toolOptions: normalizedToolOptions,
      cores
    });
    const effectiveTiming = result.effectiveTiming ?? selectToolEffectiveTime(result.parsedOutput, result.runexecParsed);
    const outputTiming = {
      walltime_ms: effectiveTiming.walltimeMs,
      cputime_ms: effectiveTiming.cputimeMs,
      memory_bytes: effectiveTiming.memoryBytes
    };
    if (!hasCompleteTiming(outputTiming)) {
      return buildToolInfraResult({ toolId, result, effectiveTiming, normalizedToolOptions });
    }
    return {
      status: 'completed',
      toolId,
      elapsedMs: effectiveTiming.time ?? result.durationMs,
      output: {
        ...(result.parsedOutput || {}),
        time: effectiveTiming.time,
        time_source: effectiveTiming.timeSource,
        walltime_ms: effectiveTiming.walltimeMs,
        cputime_ms: effectiveTiming.cputimeMs,
        memory_bytes: effectiveTiming.memoryBytes
      },
      rawOutput: result.rawOutput,
      stdout: result.stdout || '',
      stderr: result.stderr || '',
      logs: [
        ...result.stdout ? [{ stream: 'stdout', content: clampToolLog(result.stdout) }] : [],
        ...result.stderr ? [{ stream: 'stderr', content: clampToolLog(result.stderr) }] : []
      ],
      normalizedToolOptions
    };
  } catch (error) {
    return {
      status: error.inconclusive ? 'inconclusive' : 'failed',
      toolId,
      elapsedMs: error.time ?? (error.durationMs || null),
      rawOutput: error.rawOutput || null,
      stdout: error.stdout || '',
      stderr: error.stderr || '',
      logs: [
        ...error.stdout ? [{ stream: 'stdout', content: clampToolLog(error.stdout) }] : [],
        ...error.stderr ? [{ stream: 'stderr', content: clampToolLog(error.stderr) }] : []
      ],
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
        stdout: clampToolLog(error.stdout),
        stderr: clampToolLog(error.stderr),
        runexecStdout: error.runexecStdout || '',
        runexecStderr: error.runexecStderr || '',
        programOutputTail: error.programOutputTail || clampToolLog(error.stdout)
      },
      output: error.parsedOutput || undefined,
      normalizedToolOptions
    };
  }
}

async function runEngineBatch(payload = {}) {
  const regex = typeof payload.regex === 'string' ? payload.regex.trim() : '';
  const engineId = String(payload.engineId || '').trim();
  const attack = payload.attack;
  const matchMode = Number(payload.matchMode) === 1 ? 1 : 0;

  if (!regex) {
    throw new Error('regex is required.');
  }
  if (!ENGINE_DEFINITIONS[engineId]) {
    throw new Error(`Unsupported engine: ${engineId}`);
  }
  if (!attack || typeof attack !== 'object') {
    throw new Error('attack is required.');
  }

  const timeoutMs = normalizeTimeoutMs(payload.timeoutSeconds, DEFAULT_OPTIONS.engineTimeoutMs);
  const cpuCores = normalizePositiveNumber(payload.cpuCores);
  const memoryMB = normalizePositiveNumber(payload.memoryMB);
  const cores = normalizeCoreList(payload.cores);
  const repeatOverride = normalizePositiveNumber(payload.repeatOverride);
  const maxAttackLength = normalizePositiveNumber(payload.maxAttackLength) || DEFAULT_OPTIONS.maxAttackLength;
  const maxRepeatTimes = normalizePositiveNumber(payload.maxRepeatTimes) || DEFAULT_OPTIONS.maxRepeatTimes;

  const { attackText, payloadInfo } = buildAttackPayload(attack, {
    repeatOverride,
    maxRepeatTimes,
    maxAttackLength
  });

  if (!attackText || !attackText.length) {
    return {
      status: 'failed',
      engineId,
      elapsedMs: null,
      stdout: '',
      stderr: '',
      logs: [],
      error: {
        message: 'Generated attack string is empty.',
        stdout: '',
        stderr: ''
      },
      metadata: {
        payloadInfo,
        payloadPreview: ''
      }
    };
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `redos-batch-engine-${engineId}-`));
  const payloadPath = path.join(tempDir, 'payload.txt');
  await fs.writeFile(payloadPath, attackText, 'utf8');
  const regexBase64 = encodeEngineRegex(regex);

  try {
    const result = await executeEngine(
      engineId,
      payloadPath,
      regexBase64,
      matchMode,
      timeoutMs,
      { cpuCores, memoryMB, cores }
    );
    const parsed = result.parsedOutput ?? parseEngineOutput(result.stdout);
    const effectiveTiming = result.effectiveTiming ?? selectEffectiveTime(parsed, result.runexecParsed);
    return {
      status: 'completed',
      engineId,
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
      rawOutput: result.stdout?.trim() || '',
      stdout: result.stdout || '',
      stderr: result.stderr || '',
      logs: [
        ...result.stdout ? [{ stream: 'stdout', content: clampEngineLog(result.stdout) }] : [],
        ...result.stderr ? [{ stream: 'stderr', content: clampEngineLog(result.stderr) }] : []
      ],
      metadata: {
        payloadInfo,
        payloadPreview: attackText.slice(0, 256),
        attackSource: payload.attackSource || {}
      }
    };
  } catch (error) {
    return {
      status: error.inconclusive ? 'inconclusive' : 'failed',
      engineId,
      elapsedMs: null,
      stdout: error.stdout || '',
      stderr: error.stderr || '',
      logs: [
        ...error.stdout ? [{ stream: 'stdout', content: clampEngineLog(error.stdout) }] : [],
        ...error.stderr ? [{ stream: 'stderr', content: clampEngineLog(error.stderr) }] : []
      ],
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
        stdout: clampEngineLog(error.stdout),
        stderr: clampEngineLog(error.stderr),
        runexecStdout: error.runexecStdout || '',
        runexecStderr: error.runexecStderr || ''
      },
      metadata: {
        payloadInfo,
        payloadPreview: attackText.slice(0, 256),
        attackSource: payload.attackSource || {}
      }
    };
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

module.exports = {
  getBatchMeta,
  runToolBatch,
  runEngineBatch
};
