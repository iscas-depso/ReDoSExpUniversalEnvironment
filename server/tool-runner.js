const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const util = require('util');
const childProcess = require('child_process');

const execFile = util.promisify(childProcess.execFile);

const { TOOL_DEFINITIONS, DEFAULT_OPTIONS } = require('./definitions');
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
  return `${text.slice(0, LOG_LIMIT)}…`;
}

function encodeRegex(regexJson) {
  let obj, pattern;
  try {
    obj = JSON.parse(regexJson);
    //从pattern或者input中获取pattern
    if (typeof obj.pattern === 'string') {
      pattern = obj.pattern;
    } else if (typeof obj.input === 'string') {
      pattern = obj.input;
    } else {
      throw new Error('pattern 或 input 字段不存在或不是字符串');
    }
  } catch (e) {
    return Buffer.from(regexJson, 'utf8').toString('base64');
  }

  return Buffer.from(pattern, 'utf8').toString('base64');
}

function prepResult(jobManager, job, toolId, statusUpdates = {}) {
  return jobManager.updateResult(job, toolId, result => {
    Object.assign(result, statusUpdates);
  });
}

async function executeTool(toolId, regexBase64, timeoutMs, { cpuAllocator, cpuCores, memoryMB } = {}) {
  const definition = TOOL_DEFINITIONS[toolId];
  if (!definition) {
    throw new Error(`Unknown tool: ${toolId}`);
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `redos-tool-${toolId}-`));
  const outputPath = path.join(tempDir, 'output.json');
  const programOutputPath = path.join(tempDir, 'output.log');

  const { file, args, options = {} } = definition.buildCommand(regexBase64, outputPath);
  const start = Date.now();
  let stdout = '';
  let stderr = '';
  let parsedOutput = null;
  let rawOutput = null;
  let allocated = null;

  try {
    if (cpuAllocator && Number.isFinite(cpuCores) && cpuCores > 0) {
      allocated = await cpuAllocator.acquire(cpuCores);
    }

    const useRunexec = process.env.DISABLE_RUNEXEC !== '1';
    if (useRunexec) {
      const r = await runWithRunexec({
        cmd: file,
        args,
        cwd: options.cwd,
        env: options.env || {},
        outputLogPath: programOutputPath,
        timelimitSeconds: timeoutMs ? Math.floor(timeoutMs / 1000) : undefined,
        walltimelimitSeconds: timeoutMs ? Math.floor(timeoutMs / 1000) : undefined,
        memoryMB,
        cores: allocated?.cores
      });
      // Program output is redirected to programOutputPath
      try {
        stdout = await fs.readFile(programOutputPath, 'utf8');
      } catch {
        stdout = '';
      }
      stderr = '';
    } else {
      const execOptions = {
        cwd: options.cwd,
        env: { ...process.env, ...(options.env || {}) },
        timeout: timeoutMs,
        maxBuffer: 20 * 1024 * 1024
      };
      const result = await execFile(file, args, execOptions);
      stdout = result.stdout || '';
      stderr = result.stderr || '';
    }

    rawOutput = await fs.readFile(outputPath, 'utf8');
    parsedOutput = JSON.parse(rawOutput);
  } catch (error) {
    if (error.stdout) {
      stdout = error.stdout;
    }
    if (error.stderr) {
      stderr = error.stderr;
    }
    try {
      const maybeRaw = await fs.readFile(outputPath, 'utf8');
      rawOutput = maybeRaw;
      parsedOutput = JSON.parse(maybeRaw);
    } catch {
      // ignore read/parse errors
    }
    throw Object.assign(new Error(error.message || 'Tool execution failed'), {
      cause: error,
      stdout,
      stderr,
      rawOutput,
      durationMs: Date.now() - start
    });
  } finally {
    try { allocated?.release(); } catch { }
    await fs.rm(tempDir, { recursive: true, force: true });
  }

  return {
    stdout,
    stderr,
    parsedOutput,
    rawOutput,
    durationMs: Date.now() - start
  };
}

async function runToolsJob(jobManager, job, { regex, toolIds, timeoutMs, cpuAllocator, cpuCores, memoryMB }) {
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
      const result = await executeTool(toolId, regexBase64, effectiveTimeout, { cpuAllocator, cpuCores, memoryMB });

      prepResult(jobManager, job, toolId, {
        status: 'completed',
        finishedAt: new Date().toISOString(),
        elapsedMs: result.parsedOutput?.elapsed_ms ?? result.durationMs,
        output: result.parsedOutput,
        rawOutput: result.rawOutput,
        logs: [
          ...result.stdout ? [{ stream: 'stdout', content: clampLog(result.stdout) }] : [],
          ...result.stderr ? [{ stream: 'stderr', content: clampLog(result.stderr) }] : []
        ]
      });
    } catch (error) {
      prepResult(jobManager, job, toolId, {
        status: 'failed',
        finishedAt: new Date().toISOString(),
        elapsedMs: error.durationMs || null,
        error: {
          message: error.message,
          stdout: clampLog(error.stdout),
          stderr: clampLog(error.stderr)
        },
        rawOutput: error.rawOutput,
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

  const hasFailure = job.results.some(result => result.status === 'failed');
  const finalStatus = hasFailure ? 'completed_with_errors' : 'completed';
  jobManager.finalizeJob(job, finalStatus);
}

module.exports = {
  runToolsJob
};
