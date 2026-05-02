const { after, before, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

describe('Batch CLI integration', () => {
  let tempDir;
  let backendPath;
  let backendLogPath;
  let inputPath;
  let failInputPath;
  let dbPath;
  let failDbPath;
  let env;

  before(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'redos-batch-cli-'));
    backendPath = path.join(tempDir, 'fake-backend.js');
    backendLogPath = path.join(tempDir, 'backend-log.jsonl');
    inputPath = path.join(tempDir, 'regexes.txt');
    dbPath = path.join(tempDir, 'results.db');

    await fs.writeFile(inputPath, '(a+)+\n', 'utf8');
    await fs.writeFile(failInputPath = path.join(tempDir, 'failed-regexes.txt'), 'FAIL\n', 'utf8');
    failDbPath = path.join(tempDir, 'failed-results.db');
    await fs.writeFile(backendPath, `#!/usr/bin/env node
const fs = require('node:fs');

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const text = Buffer.concat(chunks).toString('utf8').trim();
  return text ? JSON.parse(text) : {};
}

function writeJson(payload) {
  process.stdout.write(JSON.stringify(payload) + '\\n');
}

function logPayload(command, payload) {
  const logPath = process.env.BATCH_BACKEND_LOG_FILE;
  if (!logPath) {
    return;
  }
  fs.appendFileSync(logPath, JSON.stringify({ command, payload }) + '\\n');
}

async function main() {
  const command = process.argv[2];
  if (command === 'meta') {
    writeJson({
      tools: [
        { id: 'regexploit', label: 'RegExploit' },
        { id: 'grewia', label: 'GREWIA' }
      ],
      engines: [
        { id: 'python', label: 'Python', available: true },
        { id: 'nodejs21', label: 'Node.js 21', available: true }
      ],
      matchModes: [
        { id: 0, label: 'Partial' },
        { id: 1, label: 'Full' }
      ],
      defaults: {
        toolTimeoutSeconds: 600,
        engineTimeoutSeconds: 120,
        maxRepeatTimes: 8192,
        maxAttackLength: 500000
      }
    });
    return;
  }

  const payload = await readStdin();
  if (command === 'run-tool') {
    logPayload(command, payload);
    if (payload.regex === 'FAIL') {
      writeJson({
        status: 'failed',
        toolId: payload.toolId,
        elapsedMs: 60,
        output: {
          elapsed_ms: 60,
          time: 60000,
          time_source: 'runexec_walltime',
          walltime_ms: 60000,
          cputime_ms: 59800,
          memory_bytes: 8192,
          is_redos: false,
          error: {
            type: 'timeout',
            message: 'Tool timed out.',
            terminationReason: 'walltime',
            returnValue: 124
          }
        },
        rawOutput: '{"error":"timeout"}',
        stdout: 'partial stdout',
        stderr: 'timeout stderr',
        logs: [{ stream: 'stderr', content: 'timeout stderr' }],
        error: {
          type: 'timeout',
          message: 'Tool timed out.',
          terminationReason: 'walltime',
          returnValue: 124,
          time: 60000,
          timeSource: 'runexec_walltime',
          walltimeMs: 60000,
          cputimeMs: 59800,
          memoryBytes: 8192
        }
      });
      return;
    }
    if (payload.toolId === 'grewia') {
      writeJson({
        status: 'completed',
        toolId: 'grewia',
        elapsedMs: 12,
        output: {
          elapsed_ms: 12,
          time: 12,
          time_source: 'tool',
          walltime_ms: 18,
          cputime_ms: 11,
          memory_bytes: 4096,
          is_redos: true,
          prefix: '',
          infix: '',
          suffix: '',
          repeat_times: -1,
          recommendedCandidateId: 'candidate-2',
          candidates: [
            {
              id: 'candidate-1',
              label: 'Full candidate',
              attack: {
                fullText: Buffer.from('aaaab', 'utf8').toString('base64')
              },
              preview: 'aaaab',
              payloadLength: 5,
              metadata: { source: 'fullText' }
            },
            {
              id: 'candidate-2',
              label: 'Pattern candidate',
              attack: {
                prefix: Buffer.from('', 'utf8').toString('base64'),
                infix: Buffer.from('a', 'utf8').toString('base64'),
                suffix: Buffer.from('!', 'utf8').toString('base64'),
                repeat_times: 8
              },
              preview: 'aaaa!',
              payloadLength: 5,
              metadata: { source: 'pattern' }
            }
          ],
          toolMeta: {
            normalizedOptions: payload.toolOptions || {},
            candidateCount: 2
          }
        },
        rawOutput: '{"tool":"grewia"}',
        stdout: 'grewia stdout',
        stderr: '',
        logs: [{ stream: 'stdout', content: 'grewia stdout' }]
      });
      return;
    }

    writeJson({
      status: 'completed',
      toolId: 'regexploit',
      elapsedMs: 7,
      output: {
        elapsed_ms: 7,
        time: 7,
        time_source: 'tool',
        walltime_ms: 9,
        cputime_ms: 6,
        memory_bytes: 2048,
        is_redos: true,
        prefix: Buffer.from('', 'utf8').toString('base64'),
        infix: Buffer.from('x', 'utf8').toString('base64'),
        suffix: Buffer.from('y', 'utf8').toString('base64'),
        repeat_times: 4
      },
      rawOutput: '{"tool":"regexploit"}',
      stdout: 'regexploit stdout',
      stderr: '',
      logs: [{ stream: 'stdout', content: 'regexploit stdout' }]
    });
    return;
  }

  if (command === 'run-engine') {
    logPayload(command, payload);
    const attack = payload.attack || {};
    const attackMode = attack.fullText ? 'fullText' : 'pattern';
    writeJson({
      status: 'completed',
      engineId: payload.engineId,
      elapsedMs: 9,
      output: {
        elapsed_ms: 9,
        match_count: attackMode === 'fullText' ? 2 : 1,
        raw: '9 - 1'
      },
      rawOutput: '9 - 1',
      stdout: '9 - 1\\n',
      stderr: '',
      logs: [{ stream: 'stdout', content: '9 - 1' }],
      metadata: {
        payloadInfo: {
          mode: attackMode
        },
        payloadPreview: attackMode,
        attackSource: payload.attackSource || {}
      }
    });
    return;
  }

  process.stderr.write('unsupported command\\n');
  process.exit(1);
}

main().catch((error) => {
  process.stderr.write(String(error && error.stack || error) + '\\n');
  process.exit(1);
});
`, 'utf8');

    env = {
      ...process.env,
      BATCH_BACKEND_BIN: process.execPath,
      BATCH_BACKEND_SCRIPT: backendPath,
      BATCH_BACKEND_LOG_FILE: backendLogPath,
      BATCH_VISIBLE_CPU_IDS: '4-5'
    };
  });

  after(async () => {
    if (tempDir) {
      await fs.rm(tempDir, { recursive: true, force: true });
    }
  });

  function runCommand(args) {
    const completed = spawnSync(args[0], args.slice(1), {
      cwd: path.resolve(__dirname, '../..'),
      env,
      encoding: 'utf8'
    });
    if (completed.status !== 0) {
      throw new Error(`Command failed: ${args.join(' ')}\nstdout:\n${completed.stdout}\nstderr:\n${completed.stderr}`);
    }
    return completed;
  }

  function runPythonSql(dbFile, sql) {
    runCommand([
      'python3',
      '-c',
      'import sqlite3, sys; conn = sqlite3.connect(sys.argv[1]); conn.executescript(sys.argv[2]); conn.commit(); conn.close()',
      dbFile,
      sql
    ]);
  }

  function queryRows(sql, params = [], targetDbPath = dbPath) {
    const probe = `
import json, sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
rows = conn.execute(sys.argv[2], json.loads(sys.argv[3])).fetchall()
print(json.dumps([dict(row) for row in rows], ensure_ascii=False))
`;
    const completed = spawnSync('python3', ['-c', probe, targetDbPath, sql, JSON.stringify(params)], {
      encoding: 'utf8'
    });
    if (completed.status !== 0) {
      throw new Error(completed.stderr || completed.stdout);
    }
    return JSON.parse(completed.stdout.trim() || '[]');
  }

  async function readBackendLogs() {
    try {
      const text = await fs.readFile(backendLogPath, 'utf8');
      return text
        .split('\n')
        .map(line => line.trim())
        .filter(Boolean)
        .map(line => JSON.parse(line));
    } catch (error) {
      if (error.code === 'ENOENT') {
        return [];
      }
      throw error;
    }
  }

  it('Gen.py and Verify.py persist legacy and GREWIA candidates into SQLite', async () => {
    runCommand([
      'python3',
      'Gen.py',
      inputPath,
      dbPath,
      '--workers',
      '2',
      '--cpu-cores',
      '1',
      '--tool-option',
      'grewia.regexEngine=Python',
      '--tool-option',
      'grewia.candidateMode=multiple'
    ]);

    const attackResults = queryRows(
      'SELECT tool, status, is_redos, repeat_times, time, time_source, walltime_ms, cputime_ms, memory_bytes FROM attack_result ORDER BY tool'
    );
    assert.deepStrictEqual(attackResults, [
      { tool: 'grewia', status: 'completed', is_redos: 1, repeat_times: -1, time: 12, time_source: 'tool', walltime_ms: 18, cputime_ms: 11, memory_bytes: 4096 },
      { tool: 'regexploit', status: 'completed', is_redos: 1, repeat_times: 4, time: 7, time_source: 'tool', walltime_ms: 9, cputime_ms: 6, memory_bytes: 2048 }
    ]);

    const candidates = queryRows(
      'SELECT tool, candidate_id, candidate_label, is_recommended, attack_type FROM attack_candidate ORDER BY candidate_id'
    );
    assert.deepStrictEqual(candidates, [
      {
        tool: 'grewia',
        candidate_id: 'candidate-1',
        candidate_label: 'Full candidate',
        is_recommended: 0,
        attack_type: 'fullText'
      },
      {
        tool: 'grewia',
        candidate_id: 'candidate-2',
        candidate_label: 'Pattern candidate',
        is_recommended: 1,
        attack_type: 'pattern'
      }
    ]);

    const metaRows = queryRows('SELECT key FROM batch_meta ORDER BY key');
    assert.ok(metaRows.some(row => row.key === 'schema_version'));
    assert.ok(metaRows.some(row => row.key === 'gen_args'));
    assert.ok(metaRows.some(row => row.key === 'runtime_cpu_info'));

    const toolLogs = (await readBackendLogs()).filter(entry => entry.command === 'run-tool');
    assert.strictEqual(toolLogs.length, 2);
    assert.deepStrictEqual(
      toolLogs.map(entry => entry.payload.cores).sort((left, right) => left[0] - right[0]),
      [[4], [5]]
    );

    runCommand([
      'python3',
      'Verify.py',
      dbPath,
      '64',
      '0',
      '--workers',
      '2',
      '--cpu-cores',
      '1'
    ]);

    const verifyRecommended = queryRows(
      'SELECT tool, engine, candidate_id FROM verify_result ORDER BY tool, engine, candidate_id'
    );
    assert.deepStrictEqual(verifyRecommended, [
      { tool: 'grewia', engine: 'nodejs21', candidate_id: 'candidate-2' },
      { tool: 'grewia', engine: 'python', candidate_id: 'candidate-2' },
      { tool: 'regexploit', engine: 'nodejs21', candidate_id: 'legacy' },
      { tool: 'regexploit', engine: 'python', candidate_id: 'legacy' }
    ]);

    const verifySources = queryRows(
      'SELECT attack_source_json FROM verify_result WHERE tool = ? ORDER BY engine',
      ['grewia']
    );
    assert.deepStrictEqual(
      verifySources.map(row => JSON.parse(row.attack_source_json)),
      [
        {
          toolId: 'grewia',
          candidateId: 'candidate-2',
          candidateLabel: 'Pattern candidate'
        },
        {
          toolId: 'grewia',
          candidateId: 'candidate-2',
          candidateLabel: 'Pattern candidate'
        }
      ]
    );

    const verifyTiming = queryRows(
      'SELECT engine, elapsed_ms, time, time_source, error_type, termination_reason, return_value FROM verify_result ORDER BY tool, engine, candidate_id'
    );
    assert.deepStrictEqual(verifyTiming, [
      { engine: 'nodejs21', elapsed_ms: 9, time: 9, time_source: null, error_type: null, termination_reason: null, return_value: null },
      { engine: 'python', elapsed_ms: 9, time: 9, time_source: null, error_type: null, termination_reason: null, return_value: null },
      { engine: 'nodejs21', elapsed_ms: 9, time: 9, time_source: null, error_type: null, termination_reason: null, return_value: null },
      { engine: 'python', elapsed_ms: 9, time: 9, time_source: null, error_type: null, termination_reason: null, return_value: null }
    ]);

    const engineLogs = (await readBackendLogs()).filter(entry => entry.command === 'run-engine');
    assert.ok(engineLogs.length >= 4);
    assert.ok(engineLogs.every(entry => Array.isArray(entry.payload.cores)));
    assert.ok(engineLogs.every(entry => entry.payload.cores.length === 1));
    assert.ok(engineLogs.every(entry => [4, 5].includes(entry.payload.cores[0])));

    runCommand([
      'python3',
      'Verify.py',
      dbPath,
      '64',
      '0',
      '--workers',
      '2',
      '--candidate-policy',
      'all'
    ]);

    const verifyAll = queryRows(
      'SELECT tool, engine, candidate_id FROM verify_result ORDER BY tool, engine, candidate_id'
    );
    assert.deepStrictEqual(verifyAll, [
      { tool: 'grewia', engine: 'nodejs21', candidate_id: 'candidate-1' },
      { tool: 'grewia', engine: 'nodejs21', candidate_id: 'candidate-2' },
      { tool: 'grewia', engine: 'python', candidate_id: 'candidate-1' },
      { tool: 'grewia', engine: 'python', candidate_id: 'candidate-2' },
      { tool: 'regexploit', engine: 'nodejs21', candidate_id: 'legacy' },
      { tool: 'regexploit', engine: 'python', candidate_id: 'legacy' }
    ]);
  });

  it('Gen.py persists structured failure fields for failed tool runs', () => {
    runCommand([
      'python3',
      'Gen.py',
      failInputPath,
      failDbPath,
      '--tools',
      'grewia'
    ]);

    const rows = queryRows(
      'SELECT status, error_type, termination_reason, return_value, time, time_source, walltime_ms, cputime_ms, memory_bytes FROM attack_result',
      [],
      failDbPath
    );
    assert.deepStrictEqual(rows, [
      {
        status: 'failed',
        error_type: 'timeout',
        termination_reason: 'walltime',
        return_value: 124,
        time: 60000,
        time_source: 'runexec_walltime',
        walltime_ms: 60000,
        cputime_ms: 59800,
        memory_bytes: 8192
      }
    ]);
  });

  it('Verify.py skips inconclusive generation results', () => {
    runCommand([
      'python3',
      'Gen.py',
      inputPath,
      dbPath,
      '--workers',
      '1'
    ]);

    runPythonSql(
      dbPath,
      "UPDATE attack_result SET status = 'inconclusive', error_type = 'infra_error' WHERE tool = 'grewia';"
    );

    runCommand([
      'python3',
      'Verify.py',
      dbPath,
      '64',
      '0',
      '--workers',
      '1'
    ]);

    const verifyRows = queryRows(
      'SELECT DISTINCT tool FROM verify_result ORDER BY tool'
    );
    assert.deepStrictEqual(verifyRows, [
      { tool: 'regexploit' }
    ]);
  });
});
