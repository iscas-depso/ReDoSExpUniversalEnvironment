const { after, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const execFileAsync = promisify(execFile);
const repoRoot = path.resolve(__dirname, '../..');
const tempPaths = [];

function encodeRegex(regex) {
  return Buffer.from(regex, 'utf8').toString('base64');
}

async function makeBinaryPayload(bytes) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'redos-engine-binary-'));
  const file = path.join(dir, 'payload.bin');
  await fs.writeFile(file, Buffer.from(bytes));
  tempPaths.push(file, dir);
  return file;
}

function parseBenchmarkOutput(stdout) {
  const match = String(stdout).trim().match(/^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+)$/);
  assert.ok(match, `unexpected benchmark output: ${stdout}`);
  return {
    elapsedMs: Number(match[1]),
    matchCount: Number(match[2])
  };
}

async function runBenchmark(relativeBinaryPath, regex, payloadPath, matchMode) {
  return execFileAsync(
    path.join(repoRoot, relativeBinaryPath),
    [encodeRegex(regex), payloadPath, String(matchMode)],
    { encoding: 'utf8' }
  );
}

after(async () => {
  while (tempPaths.length > 0) {
    const target = tempPaths.pop();
    await fs.rm(target, { recursive: true, force: true });
  }
});

describe('binary-safe engine wrappers', () => {
  it('grep preserves NUL bytes in partial mode instead of failing with an empty-file error', async () => {
    const payload = await makeBinaryPayload([0x41, 0x00, 0x42, 0x85, 0x43]);
    const { stdout, stderr } = await runBenchmark('engines/grep/bin/benchmark', 'A|B|C', payload, 0);
    const result = parseBenchmarkOutput(stdout);

    assert.strictEqual(result.matchCount, 3);
    assert.strictEqual(stderr, '');
  });

  it('grep fails clearly in full-match mode when the payload contains NUL bytes', async () => {
    const payload = await makeBinaryPayload([0x41, 0x00, 0x42]);

    await assert.rejects(
      runBenchmark('engines/grep/bin/benchmark', 'A.*B', payload, 1),
      error => {
        assert.match(error.stderr, /does not support payloads containing NUL bytes/);
        return true;
      }
    );
  });

  it('awk preserves NUL bytes in partial mode without multibyte warnings', async () => {
    const payload = await makeBinaryPayload([0x41, 0x00, 0x42, 0x85, 0x43]);
    const { stdout, stderr } = await runBenchmark('engines/awk/bin/benchmark', 'A|B|C', payload, 0);
    const result = parseBenchmarkOutput(stdout);

    assert.strictEqual(result.matchCount, 3);
    assert.strictEqual(stderr, '');
  });
});
