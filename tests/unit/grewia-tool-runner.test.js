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
      GREWIA_REGEX_ENGINE: 'Python',
      GREWIA_MATCH_MODE: '1',
      GREWIA_ATTACK_STRING_LENGTH: '4096',
      GREWIA_CANDIDATE_MODE: 'multiple',
      GREWIA_DECREMENTAL: '1'
    });
    assert.strictEqual(calls[0].timelimitSeconds, 4);
    assert.strictEqual(calls[0].walltimelimitSeconds, 4);
    assert.strictEqual(job.results[0].status, 'completed');
    assert.strictEqual(job.results[0].output.toolMeta.normalizedOptions.regexEngine, 'Python');
    assert.strictEqual(job.results[0].output.candidates[0].attack.fullText, Buffer.from('aaaaab', 'utf8').toString('base64'));
    assert.deepStrictEqual(job.results[0].logs, [
      { stream: 'stdout', content: 'stub stdout for GREWIA' }
    ]);
  });
});
