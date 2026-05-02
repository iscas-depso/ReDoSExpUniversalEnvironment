const { describe, it, afterEach } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs/promises');
const Module = require('node:module');

const JobManager = require('../../server/job-manager');
const { TOOL_DEFINITIONS } = require('../../server/definitions');

const toolRunnerPath = require.resolve('../../server/tool-runner');
const runexecPath = require.resolve('../../server/runexec');
const originalToolRunner = require.cache[toolRunnerPath];
const originalRunexec = require.cache[runexecPath];

function loadToolRunnerWithRunexec(runWithRunexec) {
  delete require.cache[toolRunnerPath];
  delete require.cache[runexecPath];

  const mockRunexecModule = new Module(runexecPath);
  mockRunexecModule.filename = runexecPath;
  mockRunexecModule.loaded = true;
  mockRunexecModule.exports = { runWithRunexec };
  require.cache[runexecPath] = mockRunexecModule;

  return require('../../server/tool-runner');
}

function restoreModules() {
  delete require.cache[toolRunnerPath];
  delete require.cache[runexecPath];
  if (originalToolRunner) {
    require.cache[toolRunnerPath] = originalToolRunner;
  }
  if (originalRunexec) {
    require.cache[runexecPath] = originalRunexec;
  }
}

afterEach(() => {
  restoreModules();
});

describe('GREWIA tool command plumbing', () => {
  it('buildCommand encodes normalized GREWIA options into env vars', () => {
    const command = TOOL_DEFINITIONS.grewia.buildCommand(
      'ZEdWemRBPT0=',
      '/tmp/grewia-output.json',
      {
        regexEngine: 'Python',
        matchMode: 1,
        attackStringLength: 4096,
        candidateMode: 'multiple',
        decremental: true
      }
    );

    assert.ok(command.args[0].endsWith('/tools/grewia/run.py'));
    assert.strictEqual(command.args[1], 'ZEdWemRBPT0=');
    assert.strictEqual(command.args[2], '/tmp/grewia-output.json');
    assert.ok(command.options.cwd.endsWith('/tools/grewia'));
    assert.deepStrictEqual(command.options.env, {
      GREWIA_REGEX_ENGINE: 'Python',
      GREWIA_MATCH_MODE: '1',
      GREWIA_ATTACK_STRING_LENGTH: '4096',
      GREWIA_CANDIDATE_MODE: 'multiple',
      GREWIA_DECREMENTAL: '1'
    });
  });

  it('runToolsJob forwards GREWIA toolOptions into the command environment and preserves output/logs', async () => {
    const calls = [];
    const { runToolsJob } = loadToolRunnerWithRunexec(async ({
      cmd,
      args,
      cwd,
      env,
      outputLogPath,
      timelimitSeconds,
      walltimelimitSeconds
    }) => {
      calls.push({ cmd, args, cwd, env, timelimitSeconds, walltimelimitSeconds });
      await fs.writeFile(outputLogPath, 'stub stdout for GREWIA', 'utf8');
      await fs.writeFile(args[2], JSON.stringify({
        elapsed_ms: 17,
        is_redos: true,
        prefix: '',
        infix: '',
        suffix: '',
        repeat_times: -1,
        recommendedCandidateId: 'candidate-1',
        candidates: [
          {
            id: 'candidate-1',
            label: 'Candidate 1',
            attack: {
              fullText: Buffer.from('aaaaab', 'utf8').toString('base64')
            },
            preview: 'aaaaab',
            payloadLength: 6
          }
        ],
        toolMeta: {
          normalizedOptions: {
            regexEngine: env.GREWIA_REGEX_ENGINE,
            matchMode: Number(env.GREWIA_MATCH_MODE),
            attackStringLength: Number(env.GREWIA_ATTACK_STRING_LENGTH),
            candidateMode: env.GREWIA_CANDIDATE_MODE,
            decremental: env.GREWIA_DECREMENTAL === '1'
          },
          candidateCount: 1
        }
      }), 'utf8');
      return {
        stdout: '',
        stderr: '',
        parsed: {
          walltime: '1.25s',
          cputime: '1.10s',
          memory: '4096B',
          returnValue: 0,
          terminationReason: null
        }
      };
    });

    const jobManager = new JobManager({ enableCleanup: false });
    const job = jobManager.createJob({
      type: 'tools',
      items: [
        {
          id: 'grewia',
          label: 'GREWIA',
          description: 'test'
        }
      ]
    });

    await runToolsJob(jobManager, job, {
      regex: '(a+)+',
      toolIds: ['grewia'],
      toolOptions: {
        grewia: {
          regexEngine: 'Python',
          matchMode: 1,
          attackStringLength: 4096,
          candidateMode: 'multiple',
          decremental: true
        }
      },
      timeoutMs: 4000
    });

    assert.strictEqual(job.status, 'completed');
    assert.strictEqual(calls.length, 1);
    assert.ok(calls[0].args[0].endsWith('/tools/grewia/run.py'));
    assert.strictEqual(calls[0].args[1], Buffer.from('(a+)+', 'utf8').toString('base64'));
    assert.ok(calls[0].cwd.endsWith('/tools/grewia'));
    assert.deepStrictEqual(calls[0].env, {
      TOOL_TIMEOUT_SECONDS: '4',
      GREWIA_TIMEOUT_SECONDS: '4',
      GREWIA_REGEX_ENGINE: 'Python',
      GREWIA_MATCH_MODE: '1',
      GREWIA_ATTACK_STRING_LENGTH: '4096',
      GREWIA_CANDIDATE_MODE: 'multiple',
      GREWIA_DECREMENTAL: '1'
    });
    assert.strictEqual(calls[0].timelimitSeconds, undefined);
    assert.strictEqual(calls[0].walltimelimitSeconds, 19);
    assert.strictEqual(job.results[0].status, 'completed');
    assert.strictEqual(job.results[0].output.toolMeta.normalizedOptions.regexEngine, 'Python');
    assert.strictEqual(job.results[0].output.candidates[0].attack.fullText, Buffer.from('aaaaab', 'utf8').toString('base64'));
    assert.strictEqual(job.results[0].output.time, 17);
    assert.strictEqual(job.results[0].output.time_source, 'tool');
    assert.strictEqual(job.results[0].output.walltime_ms, 1250);
    assert.strictEqual(job.results[0].output.cputime_ms, 1100);
    assert.strictEqual(job.results[0].output.memory_bytes, 4096);
    assert.deepStrictEqual(job.results[0].logs, [
      { stream: 'stdout', content: 'stub stdout for GREWIA' }
    ]);
  });

  it('classifies wrapper failures and preserves parsed error output', async () => {
    const { runToolsJob } = loadToolRunnerWithRunexec(async ({ args, outputLogPath }) => {
      await fs.writeFile(outputLogPath, 'Exception in thread "main" java.lang.StackOverflowError', 'utf8');
      await fs.writeFile(args[2], JSON.stringify({
        elapsed_ms: 33,
        is_redos: false,
        error: {
          type: 'tool_exception',
          message: 'GREWIA reported a fatal exception.',
          returnValue: 17
        }
      }), 'utf8');
      const failure = new Error('GREWIA reported a fatal exception.');
      failure.stdout = '';
      failure.stderr = 'GREWIA reported a fatal exception.';
      failure.parsed = {
        terminationReason: null,
        returnValue: 17
      };
      throw failure;
    });

    const jobManager = new JobManager({ enableCleanup: false });
    const job = jobManager.createJob({
      type: 'tools',
      items: [{ id: 'grewia', label: 'GREWIA', description: 'test' }]
    });

    await runToolsJob(jobManager, job, {
      regex: '(a+)+',
      toolIds: ['grewia'],
      timeoutMs: 4000
    });

    assert.strictEqual(job.results[0].status, 'failed');
    assert.strictEqual(job.results[0].error.type, 'tool_exception');
    assert.strictEqual(job.results[0].error.returnValue, 17);
    assert.strictEqual(job.results[0].error.time, 33);
    assert.strictEqual(job.results[0].error.timeSource, 'tool');
    assert.strictEqual(job.results[0].output.error.type, 'tool_exception');
    assert.match(job.results[0].logs[0].content, /StackOverflowError/);
  });

  it('rejects wrapper success output when runexec still reports a nonzero exit', async () => {
    const { runToolsJob } = loadToolRunnerWithRunexec(async ({ args, outputLogPath }) => {
      await fs.writeFile(outputLogPath, 'wrapper stdout', 'utf8');
      await fs.writeFile(args[2], JSON.stringify({
        elapsed_ms: 58,
        is_redos: true,
        prefix: '',
        infix: '',
        suffix: '',
        repeat_times: -1
      }), 'utf8');
      const failure = new Error('wrapped process exited nonzero');
      failure.stdout = '';
      failure.stderr = '';
      failure.parsed = {
        terminationReason: null,
        returnValue: 17
      };
      throw failure;
    });

    const jobManager = new JobManager({ enableCleanup: false });
    const job = jobManager.createJob({
      type: 'tools',
      items: [{ id: 'grewia', label: 'GREWIA', description: 'test' }]
    });

    await runToolsJob(jobManager, job, {
      regex: '(a+)+',
      toolIds: ['grewia'],
      timeoutMs: 4000
    });

    assert.strictEqual(job.status, 'completed_with_errors');
    assert.strictEqual(job.results[0].status, 'failed');
    assert.strictEqual(job.results[0].error.type, 'child_exit_nonzero');
    assert.strictEqual(job.results[0].error.returnValue, 17);
  });

  it('classifies missing output after runexec failure as tool_exception', async () => {
    const { inferErrorType } = loadToolRunnerWithRunexec(async () => ({ stdout: '', stderr: '', parsed: {} }));

    const result = inferErrorType({
      explicitType: null,
      terminationReason: 'failed',
      returnValue: null,
      stdout: '',
      stderr: '',
      programOutputTail: '',
      parsedOutput: null,
      missingOutput: true
    });

    assert.strictEqual(result, 'tool_exception');
  });

  it('marks missing runexec metrics as inconclusive and retries before giving up', async () => {
    let attempts = 0;
    const { runToolsJob } = loadToolRunnerWithRunexec(async ({ args, outputLogPath }) => {
      attempts += 1;
      await fs.writeFile(outputLogPath, 'wrapper stdout', 'utf8');
      await fs.writeFile(args[2], JSON.stringify({
        elapsed_ms: 12,
        is_redos: false,
        prefix: '',
        infix: '',
        suffix: '',
        repeat_times: -1
      }), 'utf8');
      return {
        stdout: '',
        stderr: '',
        parsed: {
          returnValue: 0,
          terminationReason: null
        }
      };
    });

    const jobManager = new JobManager({ enableCleanup: false });
    const job = jobManager.createJob({
      type: 'tools',
      items: [{ id: 'grewia', label: 'GREWIA', description: 'test' }]
    });

    await runToolsJob(jobManager, job, {
      regex: '(a+)+',
      toolIds: ['grewia'],
      timeoutMs: 4000
    });

    assert.strictEqual(job.status, 'completed_with_errors');
    assert.strictEqual(attempts, 3);
    assert.strictEqual(job.results[0].status, 'inconclusive');
    assert.strictEqual(job.results[0].error.type, 'infra_error');
    assert.match(job.results[0].error.message, /runexec did not provide complete metrics/i);
  });

  it('retries when runexec reports terminationReason failed but the wrapper output succeeded without metrics', async () => {
    let attempts = 0;
    const { runToolsJob } = loadToolRunnerWithRunexec(async ({ args, outputLogPath }) => {
      attempts += 1;
      await fs.writeFile(outputLogPath, 'wrapper stdout', 'utf8');
      await fs.writeFile(args[2], JSON.stringify({
        elapsed_ms: 33,
        is_redos: true,
        prefix: '',
        infix: '',
        suffix: '',
        repeat_times: 8
      }), 'utf8');
      return {
        stdout: '',
        stderr: '',
        parsed: {
          terminationReason: 'failed',
          returnValue: null
        }
      };
    });

    const jobManager = new JobManager({ enableCleanup: false });
    const job = jobManager.createJob({
      type: 'tools',
      items: [{ id: 'grewia', label: 'GREWIA', description: 'test' }]
    });

    await runToolsJob(jobManager, job, {
      regex: '(a+)+',
      toolIds: ['grewia'],
      timeoutMs: 4000
    });

    assert.strictEqual(job.status, 'completed_with_errors');
    assert.strictEqual(attempts, 3);
    assert.strictEqual(job.results[0].status, 'inconclusive');
    assert.strictEqual(job.results[0].error.type, 'infra_error');
    assert.strictEqual(job.results[0].output.is_redos, true);
  });
});
