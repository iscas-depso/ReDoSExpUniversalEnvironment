const { afterEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs/promises');
const Module = require('node:module');

const batchCliPath = require.resolve('../../server/batch-cli');
const toolRunnerPath = require.resolve('../../server/tool-runner');
const engineRunnerPath = require.resolve('../../server/engine-runner');

const originalBatchCli = require.cache[batchCliPath];
const originalToolRunner = require.cache[toolRunnerPath];
const originalEngineRunner = require.cache[engineRunnerPath];

function restoreModules() {
  delete require.cache[batchCliPath];
  delete require.cache[toolRunnerPath];
  delete require.cache[engineRunnerPath];

  if (originalBatchCli) {
    require.cache[batchCliPath] = originalBatchCli;
  }
  if (originalToolRunner) {
    require.cache[toolRunnerPath] = originalToolRunner;
  }
  if (originalEngineRunner) {
    require.cache[engineRunnerPath] = originalEngineRunner;
  }
}

function loadBatchCli({
  toolRunnerExports = {},
  engineRunnerExports = {}
} = {}) {
  restoreModules();

  const mockToolRunner = new Module(toolRunnerPath);
  mockToolRunner.filename = toolRunnerPath;
  mockToolRunner.loaded = true;
  mockToolRunner.exports = {
    executeTool: async () => ({
      parsedOutput: { elapsed_ms: 11, is_redos: true },
      rawOutput: '{}',
      stdout: 'tool stdout',
      stderr: '',
      runexecParsed: {
        walltime: '0.011s',
        cputime: '0.010s',
        memory: '4096B'
      },
      durationMs: 11
    }),
    selectEffectiveTime: (parsedOutput, runexecParsed) => ({
      time: parsedOutput?.elapsed_ms ?? (
        typeof runexecParsed?.walltimeMs === 'number'
          ? runexecParsed.walltimeMs
          : (typeof runexecParsed?.walltime === 'string'
            ? Number(runexecParsed.walltime.replace(/s$/, '')) * 1000
            : 0)
      ),
      timeSource: parsedOutput?.elapsed_ms != null ? 'tool' : 'runexec_walltime',
      walltimeMs: runexecParsed?.walltimeMs ?? (
        typeof runexecParsed?.walltime === 'string'
          ? Number(runexecParsed.walltime.replace(/s$/, '')) * 1000
          : null
      ),
      cputimeMs: runexecParsed?.cputimeMs ?? (
        typeof runexecParsed?.cputime === 'string'
          ? Number(runexecParsed.cputime.replace(/s$/, '')) * 1000
          : null
      ),
      memoryBytes: runexecParsed?.memoryBytes ?? (
        typeof runexecParsed?.memory === 'string'
          ? Number(runexecParsed.memory.replace(/B$/, ''))
          : null
      )
    }),
    clampLog: value => String(value),
    encodeRegex: regex => Buffer.from(regex, 'utf8').toString('base64'),
    ...toolRunnerExports
  };
  require.cache[toolRunnerPath] = mockToolRunner;

  const mockEngineRunner = new Module(engineRunnerPath);
  mockEngineRunner.filename = engineRunnerPath;
  mockEngineRunner.loaded = true;
  mockEngineRunner.exports = {
    buildAttackPayload: () => ({
      attackText: 'PAYLOAD',
      payloadInfo: { payloadLength: 7, mode: 'fullText' }
    }),
    executeEngine: async () => ({ stdout: '12.5 - 3', stderr: '', runexecParsed: {} }),
    parseEngineOutput: stdout => {
      const match = String(stdout).trim().match(/(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+)/);
      if (!match) {
        return null;
      }
      return { elapsedMs: Number(match[1]), matchCount: Number(match[2]) };
    },
    selectEffectiveTime: (parsedOutput, runexecParsed) => ({
      time: parsedOutput?.elapsedMs ?? 0,
      timeSource: parsedOutput?.elapsedMs != null ? 'engine' : 'runexec_walltime',
      walltimeMs: runexecParsed?.walltimeMs ?? null,
      cputimeMs: runexecParsed?.cputimeMs ?? null,
      memoryBytes: runexecParsed?.memoryBytes ?? null
    }),
    clampLog: value => String(value),
    encodeRegex: regex => Buffer.from(regex, 'utf8').toString('base64'),
    ...engineRunnerExports
  };
  require.cache[engineRunnerPath] = mockEngineRunner;

  return require('../../server/batch-cli');
}

afterEach(() => {
  restoreModules();
});

describe('batch-cli helpers', () => {
  it('getBatchMeta exposes current tools, engines, and defaults', () => {
    restoreModules();
    const { getBatchMeta } = require('../../server/batch-cli');
    const meta = getBatchMeta();

    assert.ok(Array.isArray(meta.tools));
    assert.ok(Array.isArray(meta.engines));
    assert.ok(Array.isArray(meta.matchModes));
    assert.ok(meta.tools.some(tool => tool.id === 'grewia'));
    assert.ok(meta.engines.some(engine => engine.id === 'python'));
    assert.strictEqual(typeof meta.defaults.maxAttackLength, 'number');
  });

  it('runToolBatch normalizes tool options and preserves output/logs', async () => {
    let received = null;
    const { runToolBatch } = loadBatchCli({
      toolRunnerExports: {
        executeTool: async (toolId, regexBase64, timeoutMs, options) => {
          received = { toolId, regexBase64, timeoutMs, options };
          return {
            parsedOutput: {
              elapsed_ms: 17,
              is_redos: true,
              recommendedCandidateId: 'candidate-1',
              candidates: [
                {
                  id: 'candidate-1',
                  label: 'Candidate 1',
                  attack: { fullText: Buffer.from('aaaaab', 'utf8').toString('base64') }
                }
              ]
            },
            rawOutput: '{"ok":true}',
            stdout: 'tool stdout',
            stderr: 'tool stderr',
            runexecParsed: {
              walltime: '0.020s',
              cputime: '0.018s',
              memory: '8192B'
            },
            durationMs: 20
          };
        }
      }
    });

    const result = await runToolBatch({
      regex: '(a+)+',
      toolId: 'grewia',
      timeoutSeconds: 9,
      cpuCores: 2,
      cores: [4, 5],
      memoryMB: 512,
      toolOptions: {
        regexEngine: 'Python',
        matchMode: 1,
        attackStringLength: 4096,
        candidateMode: 'multiple',
        decremental: true
      }
    });

    assert.strictEqual(result.status, 'completed');
    assert.strictEqual(received.toolId, 'grewia');
    assert.strictEqual(received.timeoutMs, 9000);
    assert.strictEqual(received.regexBase64, Buffer.from('(a+)+', 'utf8').toString('base64'));
    assert.deepStrictEqual(received.options.cores, [4, 5]);
    assert.deepStrictEqual(received.options.toolOptions, {
      regexEngine: 'Python',
      matchMode: 1,
      attackStringLength: 4096,
      candidateMode: 'multiple',
      decremental: true
    });
    assert.deepStrictEqual(result.normalizedToolOptions, received.options.toolOptions);
    assert.deepStrictEqual(result.logs, [
      { stream: 'stdout', content: 'tool stdout' },
      { stream: 'stderr', content: 'tool stderr' }
    ]);
    assert.deepStrictEqual(result.output, {
      elapsed_ms: 17,
      is_redos: true,
      recommendedCandidateId: 'candidate-1',
      candidates: [
        {
          id: 'candidate-1',
          label: 'Candidate 1',
          attack: { fullText: Buffer.from('aaaaab', 'utf8').toString('base64') }
        }
      ],
      time: 17,
      time_source: 'tool',
      walltime_ms: 20,
      cputime_ms: 18,
      memory_bytes: 8192
    });
    assert.strictEqual(result.output.candidates[0].label, 'Candidate 1');
  });

  it('runToolBatch falls back to runexec timing when tool output omits elapsed_ms', async () => {
    const { runToolBatch } = loadBatchCli({
      toolRunnerExports: {
        executeTool: async () => ({
          parsedOutput: {
            is_redos: false,
            prefix: '',
            infix: '',
            suffix: '',
            repeat_times: 2
          },
          rawOutput: '{"ok":true}',
          stdout: 'tool stdout',
          stderr: '',
          runexecParsed: {
            walltime: '10.5s',
            cputime: '9.2s',
            memory: '4096B'
          }
        })
      }
    });

    const result = await runToolBatch({
      regex: '(a+)+',
      toolId: 'regexploit'
    });

    assert.strictEqual(result.status, 'completed');
    assert.strictEqual(result.elapsedMs, 10500);
    assert.deepStrictEqual(result.output, {
      is_redos: false,
      prefix: '',
      infix: '',
      suffix: '',
      repeat_times: 2,
      time: 10500,
      time_source: 'runexec_walltime',
      walltime_ms: 10500,
      cputime_ms: 9200,
      memory_bytes: 4096
    });
  });

  it('runEngineBatch builds payload files and preserves attack source metadata', async () => {
    let observed = null;
    const { runEngineBatch } = loadBatchCli({
      engineRunnerExports: {
        buildAttackPayload: attack => ({
          attackText: attack.fullText ? 'FULL_TEXT_PAYLOAD' : 'LEGACY_PAYLOAD',
          payloadInfo: { payloadLength: 17, mode: attack.fullText ? 'fullText' : 'pattern' }
        }),
        executeEngine: async (engineId, payloadPath, regexBase64, matchMode, timeoutMs, options) => {
          observed = {
            engineId,
            regexBase64,
            matchMode,
            timeoutMs,
            options,
            payloadText: await fs.readFile(payloadPath, 'utf8')
          };
          return { stdout: '12.5 - 3', stderr: '' };
        }
      }
    });

    const result = await runEngineBatch({
      regex: '(a+)+',
      engineId: 'python',
      attack: { fullText: Buffer.from('aaaaab', 'utf8').toString('base64') },
      matchMode: 1,
      timeoutSeconds: 7,
      cpuCores: 3,
      cores: [6, 7, 8],
      memoryMB: 256,
      attackSource: {
        toolId: 'grewia',
        candidateId: 'candidate-1',
        candidateLabel: 'Candidate 1'
      }
    });

    assert.strictEqual(result.status, 'completed');
    assert.strictEqual(observed.engineId, 'python');
    assert.strictEqual(observed.matchMode, 1);
    assert.strictEqual(observed.timeoutMs, 7000);
    assert.strictEqual(observed.payloadText, 'FULL_TEXT_PAYLOAD');
    assert.deepStrictEqual(observed.options, { cpuCores: 3, memoryMB: 256, cores: [6, 7, 8] });
    assert.deepStrictEqual(result.output, {
      elapsed_ms: 12.5,
      match_count: 3,
      time: 12.5,
      time_source: 'engine',
      walltime_ms: null,
      cputime_ms: null,
      memory_bytes: null,
      raw: '12.5 - 3'
    });
    assert.deepStrictEqual(result.metadata.attackSource, {
      toolId: 'grewia',
      candidateId: 'candidate-1',
      candidateLabel: 'Candidate 1'
    });
  });

  it('runEngineBatch falls back to runexec walltime when engine output omits elapsed_ms', async () => {
    const { runEngineBatch } = loadBatchCli({
      engineRunnerExports: {
        executeEngine: async () => ({
          stdout: 'benchmark header only',
          stderr: '',
          parsedOutput: null,
          runexecParsed: {
            walltime: '10.5s',
            cputime: '9.2s',
            memory: '4096B'
          },
          effectiveTiming: {
            time: 10500,
            timeSource: 'runexec_walltime',
            walltimeMs: 10500,
            cputimeMs: 9200,
            memoryBytes: 4096
          }
        })
      }
    });

    const result = await runEngineBatch({
      regex: '(a+)+',
      engineId: 'python',
      attack: { fullText: Buffer.from('aaaaab', 'utf8').toString('base64') }
    });

    assert.strictEqual(result.status, 'completed');
    assert.strictEqual(result.elapsedMs, 10500);
    assert.deepStrictEqual(result.output, {
      elapsed_ms: null,
      match_count: null,
      time: 10500,
      time_source: 'runexec_walltime',
      walltime_ms: 10500,
      cputime_ms: 9200,
      memory_bytes: 4096,
      raw: 'benchmark header only'
    });
  });

  it('runToolBatch preserves structured failure metadata', async () => {
    const { runToolBatch } = loadBatchCli({
      toolRunnerExports: {
        executeTool: async () => {
          const error = new Error('RegexStatic analysis timed out after 60 seconds.');
          error.type = 'timeout';
          error.terminationReason = 'walltime';
          error.returnValue = 124;
          error.stdout = 'tool stdout';
          error.stderr = 'tool stderr';
          error.programOutputTail = 'tool stdout';
          error.parsedOutput = {
            elapsed_ms: 60000,
            is_redos: false,
            error: {
              type: 'timeout',
              message: 'RegexStatic analysis timed out after 60 seconds.',
              returnValue: 124
            }
          };
          error.rawOutput = '{"error":"timeout"}';
          throw error;
        }
      }
    });

    const result = await runToolBatch({
      regex: '(a+)+',
      toolId: 'regexstatic',
      timeoutSeconds: 60
    });

    assert.strictEqual(result.status, 'failed');
    assert.strictEqual(result.error.type, 'timeout');
    assert.strictEqual(result.error.terminationReason, 'walltime');
    assert.strictEqual(result.error.returnValue, 124);
    assert.strictEqual(result.output.error.type, 'timeout');
  });

  it('runToolBatch preserves inconclusive infra errors separately from normal failures', async () => {
    const { runToolBatch } = loadBatchCli({
      toolRunnerExports: {
        executeTool: async () => {
          const error = new Error('runexec did not provide complete metrics for successful tool execution.');
          error.type = 'infra_error';
          error.inconclusive = true;
          error.stdout = 'tool stdout';
          error.stderr = '';
          error.parsedOutput = {
            elapsed_ms: 42,
            is_redos: true
          };
          error.rawOutput = '{"ok":true}';
          throw error;
        }
      }
    });

    const result = await runToolBatch({
      regex: '(a+)+',
      toolId: 'grewia'
    });

    assert.strictEqual(result.status, 'inconclusive');
    assert.strictEqual(result.error.type, 'infra_error');
    assert.strictEqual(result.output.is_redos, true);
  });

  it('runToolBatch marks successful tool output without runexec metrics as inconclusive', async () => {
    const { runToolBatch } = loadBatchCli({
      toolRunnerExports: {
        executeTool: async () => ({
          parsedOutput: {
            elapsed_ms: 42,
            is_redos: true
          },
          rawOutput: '{"ok":true}',
          stdout: 'tool stdout',
          stderr: '',
          runexecParsed: {
            returnValue: 0,
            terminationReason: null
          },
          durationMs: 44
        })
      }
    });

    const result = await runToolBatch({
      regex: '(a+)+',
      toolId: 'grewia'
    });

    assert.strictEqual(result.status, 'inconclusive');
    assert.strictEqual(result.error.type, 'infra_error');
    assert.strictEqual(result.output.is_redos, true);
    assert.strictEqual(result.output.walltime_ms, null);
  });

  it('runEngineBatch preserves inconclusive infra errors separately from normal failures', async () => {
    const { runEngineBatch } = loadBatchCli({
      engineRunnerExports: {
        executeEngine: async () => {
          const error = new Error('runexec did not provide complete metrics for successful engine execution (java8).');
          error.type = 'infra_error';
          error.inconclusive = true;
          error.stdout = '12.5 - 1';
          error.stderr = '';
          throw error;
        }
      }
    });

    const result = await runEngineBatch({
      regex: '(a+)+',
      engineId: 'java8',
      attack: { fullText: Buffer.from('aaaaab', 'utf8').toString('base64') }
    });

    assert.strictEqual(result.status, 'inconclusive');
    assert.strictEqual(result.error.type, 'infra_error');
  });
});
