const { after, describe, it } = require('node:test');
const assert = require('node:assert');
const cp = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SOURCE_RUN_PY = path.join(REPO_ROOT, 'tools', 'regexstatic', 'run.py');
const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';
const TEMP_DIRS = [];

function makeFixture(javaBody) {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'regexstatic-wrapper-test-'));
  TEMP_DIRS.push(fixtureDir);

  fs.writeFileSync(path.join(fixtureDir, 'run.py'), fs.readFileSync(SOURCE_RUN_PY, 'utf8'), 'utf8');
  fs.mkdirSync(path.join(fixtureDir, 'target', 'dependency-jars'), { recursive: true });
  fs.writeFileSync(path.join(fixtureDir, 'target', 'regex-static-analysis-1.0-SNAPSHOT.jar'), '', 'utf8');
  const javaPath = path.join(fixtureDir, 'java');
  fs.writeFileSync(javaPath, `#!/usr/bin/env python3\n${javaBody}\n`, 'utf8');
  fs.chmodSync(javaPath, 0o755);

  return fixtureDir;
}

function runWrapper(fixtureDir, env = {}) {
  const outputPath = path.join(fixtureDir, 'output.json');
  const result = cp.spawnSync(
    PYTHON_BIN,
    [path.join(fixtureDir, 'run.py'), Buffer.from('(a+)+', 'utf8').toString('base64'), outputPath],
    {
      cwd: fixtureDir,
      encoding: 'utf8',
      env: {
        ...process.env,
        PATH: `${fixtureDir}:${process.env.PATH || ''}`,
        ...env
      },
      timeout: 10_000
    }
  );

  return {
    ...result,
    outputJson: fs.existsSync(outputPath)
      ? JSON.parse(fs.readFileSync(outputPath, 'utf8'))
      : null
  };
}

after(() => {
  TEMP_DIRS.forEach(dir => {
    fs.rmSync(dir, { recursive: true, force: true });
  });
});

describe('RegexStatic Python wrapper', () => {
  it('uses the configured timeout and exits nonzero on timeout', () => {
    const fixtureDir = makeFixture(`
import time
time.sleep(1.3)
`);
    const result = runWrapper(fixtureDir, {
      REGEXSTATIC_TIMEOUT_SECONDS: '1'
    });

    assert.strictEqual(result.status, 124, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'timeout');
    assert.strictEqual(result.outputJson.error.returnValue, 124);
  });

  it('returns structured child-exit errors', () => {
    const fixtureDir = makeFixture(`
import sys
sys.stderr.write("java failed\\n")
sys.exit(9)
`);
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 9, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'child_exit_nonzero');
    assert.strictEqual(result.outputJson.error.returnValue, 9);
  });

  it('classifies signal termination as tool_exception', () => {
    const fixtureDir = makeFixture(`
import os
import signal
os.kill(os.getpid(), signal.SIGSEGV)
`);
    const result = runWrapper(fixtureDir);

    assert.notStrictEqual(result.status, 0, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.strictEqual(result.outputJson.error.returnValue, -11);
  });
});
