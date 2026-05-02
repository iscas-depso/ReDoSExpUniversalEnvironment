const { after, describe, it } = require('node:test');
const assert = require('node:assert');
const cp = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';
const TEMP_DIRS = [];

function copyDirRecursive(sourceDir, targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(sourcePath, targetPath);
    } else {
      fs.copyFileSync(sourcePath, targetPath);
    }
  }
}

function makeFixture(toolName, { mutateRunPy, copySrc = false, extraFiles = [] } = {}) {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), `${toolName}-wrapper-test-`));
  TEMP_DIRS.push(fixtureDir);

  const sourceRunPy = path.join(REPO_ROOT, 'tools', toolName, 'run.py');
  let runPy = fs.readFileSync(sourceRunPy, 'utf8');
  if (typeof mutateRunPy === 'function') {
    runPy = mutateRunPy(runPy);
  }
  fs.writeFileSync(path.join(fixtureDir, 'run.py'), runPy, 'utf8');

  if (copySrc) {
    copyDirRecursive(path.join(REPO_ROOT, 'tools', toolName, 'src'), path.join(fixtureDir, 'src'));
  }

  for (const file of extraFiles) {
    const filePath = path.join(fixtureDir, file.relativePath);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, file.contents, 'utf8');
    if (file.mode) {
      fs.chmodSync(filePath, file.mode);
    }
  }

  return fixtureDir;
}

function runWrapper(fixtureDir, {
  regex = Buffer.from('(a+)+', 'utf8').toString('base64'),
  env = {}
} = {}) {
  const outputPath = path.join(fixtureDir, 'output.json');
  const result = cp.spawnSync(
    PYTHON_BIN,
    [path.join(fixtureDir, 'run.py'), regex, outputPath],
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
  for (const dir of TEMP_DIRS) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe('Unified wrapper failure contract', () => {
  it('rescue exits nonzero with timeout metadata', () => {
    const fixtureDir = makeFixture('rescue', {
      extraFiles: [
        { relativePath: 'target/ReScue-0.0.1-SNAPSHOT.jar', contents: '' },
        {
          relativePath: 'java',
          contents: '#!/usr/bin/env python3\nimport time\ntime.sleep(1.3)\n',
          mode: 0o755
        }
      ]
    });
    const result = runWrapper(fixtureDir, {
      env: { TOOL_TIMEOUT_SECONDS: '1' }
    });

    assert.strictEqual(result.status, 124, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'timeout');
  });

  it('rengar exits nonzero with timeout metadata', () => {
    const fixtureDir = makeFixture('rengar', {
      extraFiles: [
        { relativePath: 'Rengar.jar', contents: '' },
        {
          relativePath: 'java',
          contents: '#!/usr/bin/env python3\nimport time\ntime.sleep(1.3)\n',
          mode: 0o755
        }
      ]
    });
    const result = runWrapper(fixtureDir, {
      env: {
        TOOL_TIMEOUT_SECONDS: '1',
        JAVA_BIN: path.join(fixtureDir, 'java')
      }
    });

    assert.strictEqual(result.status, 124, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'timeout');
  });

  it('redoshunter exits nonzero with child-exit metadata', () => {
    const fixtureDir = makeFixture('redoshunter', {
      extraFiles: [
        { relativePath: 'ReDoSHunter.jar', contents: '' },
        {
          relativePath: 'java',
          contents: '#!/usr/bin/env python3\nimport sys\nsys.stderr.write("boom\\n")\nsys.exit(9)\n',
          mode: 0o755
        }
      ]
    });
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 9, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'child_exit_nonzero');
    assert.strictEqual(result.outputJson.error.returnValue, 9);
  });

  it('redoshunter classifies signal termination as tool_exception', () => {
    const fixtureDir = makeFixture('redoshunter', {
      extraFiles: [
        { relativePath: 'ReDoSHunter.jar', contents: '' },
        {
          relativePath: 'java',
          contents: '#!/usr/bin/env python3\nimport os\nimport signal\nos.kill(os.getpid(), signal.SIGABRT)\n',
          mode: 0o755
        }
      ]
    });
    const result = runWrapper(fixtureDir);

    assert.notStrictEqual(result.status, 0, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.strictEqual(result.outputJson.error.returnValue, -6);
  });

  it('regulator fails clearly when its fuzzer binary is missing', () => {
    const fixtureDir = makeFixture('regulator');
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 1, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.match(result.outputJson.error.message, /Regulator fuzzer not found/);
  });

  it('regulator gives the fuzzer the full tool timeout budget before pump verification', () => {
    const fixtureDir = makeFixture('regulator', {
      extraFiles: [
        {
          relativePath: 'regulator-dynamic/fuzzer/build/fuzzer',
          contents: [
            '#!/usr/bin/env python3',
            'import sys, time',
            'time.sleep(2.5)',
            'print(\'SUMMARY word="A" Total=500000 MaxObservation\')',
            ''
          ].join('\n'),
          mode: 0o755
        },
        {
          relativePath: 'regulator-dynamic/driver/pump.py',
          contents: [
            'fuzzer_binary = None',
            'def get_pump_report(regex_bytes, prefix, witness, width, deadline):',
            '    return {"class": "POLYNOMIAL", "pump_pos": 0, "pump_len": 1}',
            ''
          ].join('\n')
        },
        {
          relativePath: 'regulator-dynamic/driver/binsearch_pump.py',
          contents: ''
        }
      ]
    });
    const result = runWrapper(fixtureDir, {
      env: { TOOL_TIMEOUT_SECONDS: '3' }
    });

    assert.strictEqual(result.status, 0, result.stderr);
    assert.ok(result.outputJson.elapsed_ms >= 2400, result.outputJson.elapsed_ms);
    assert.strictEqual(result.outputJson.error, undefined);
  });

  it('regexploit exits nonzero on internal exceptions', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true,
      mutateRunPy(contents) {
        return contents.replace('parsed = parse_pattern_with_fallback(pattern)', 'raise RuntimeError("boom")');
      }
    });
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 1, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.match(result.outputJson.error.message, /boom/);
  });

  it('regexploit falls back to javascript-style fixes for hyphenated character classes', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true
    });
    const result = runWrapper(fixtureDir, {
      regex: Buffer.from(String.raw`([\d\w-.]+?\.example\.com)$`, 'utf8').toString('base64')
    });

    assert.strictEqual(result.status, 0, result.stderr);
    assert.ok(result.outputJson);
    assert.strictEqual(result.outputJson.error, undefined);
  });

  it('regexploit normalizes literal hyphens inside mixed character classes', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true
    });
    const result = runWrapper(fixtureDir, {
      regex: Buffer.from(String.raw`^[\w-()]+$`, 'utf8').toString('base64')
    });

    assert.strictEqual(result.status, 0, result.stderr);
    assert.ok(result.outputJson);
    assert.strictEqual(result.outputJson.error, undefined);
  });

  it('regexploit normalizes common named-group syntax variants', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true
    });
    const result = runWrapper(fixtureDir, {
      regex: Buffer.from(String.raw`^(?<word>a+)\k<word>$`, 'utf8').toString('base64')
    });

    assert.strictEqual(result.status, 0, result.stderr);
    assert.ok(result.outputJson);
    assert.strictEqual(result.outputJson.error, undefined);
  });

  it('regexploit rejects unsupported unicode property escapes clearly', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true
    });
    const result = runWrapper(fixtureDir, {
      regex: Buffer.from(String.raw`\p{N}`, 'utf8').toString('base64')
    });

    assert.strictEqual(result.status, 1, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.match(result.outputJson.error.message, /unsupported syntax/i);
  });

  it('regexploit rejects unsupported conditional groups clearly', () => {
    const fixtureDir = makeFixture('regexploit', {
      copySrc: true
    });
    const result = runWrapper(fixtureDir, {
      regex: Buffer.from(String.raw`^(?(?=a)b|c)$`, 'utf8').toString('base64')
    });

    assert.strictEqual(result.status, 1, result.stderr);
    assert.strictEqual(result.outputJson.error.type, 'tool_exception');
    assert.match(result.outputJson.error.message, /conditional groups/i);
  });
});
