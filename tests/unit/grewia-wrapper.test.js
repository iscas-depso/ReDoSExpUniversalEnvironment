const { describe, it, after } = require('node:test');
const assert = require('node:assert');
const cp = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SOURCE_RUN_PY = path.join(REPO_ROOT, 'tools', 'grewia', 'run.py');
const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';
const TEMP_DIRS = [];

function makeFixture(stubBody, { mutateRunPy } = {}) {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'grewia-wrapper-test-'));
  TEMP_DIRS.push(fixtureDir);

  fs.mkdirSync(path.join(fixtureDir, 'build'), { recursive: true });

  let runPy = fs.readFileSync(SOURCE_RUN_PY, 'utf8');
  if (typeof mutateRunPy === 'function') {
    runPy = mutateRunPy(runPy);
  }
  fs.writeFileSync(path.join(fixtureDir, 'run.py'), runPy, 'utf8');

  if (stubBody != null) {
    const exePath = path.join(fixtureDir, 'build', 'GREWIA');
    fs.writeFileSync(exePath, `#!/usr/bin/env python3\n${stubBody}\n`, 'utf8');
    fs.chmodSync(exePath, 0o755);
  }

  return fixtureDir;
}

function runWrapper(fixtureDir, {
  regex = Buffer.from('(a+)+', 'utf8').toString('base64'),
  env = {}
} = {}) {
  const outputPath = path.join(fixtureDir, 'normalized-output.json');
  const result = cp.spawnSync(
    PYTHON_BIN,
    [path.join(fixtureDir, 'run.py'), regex, outputPath],
    {
      cwd: fixtureDir,
      encoding: 'utf8',
      env: {
        ...process.env,
        ...env
      },
      timeout: 10_000
    }
  );

  return {
    ...result,
    outputPath,
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

describe('GREWIA Python wrapper', () => {
  it('loads default options, maps match mode correctly, and sorts candidate files numerically', () => {
    const fixtureDir = makeFixture(`
import json
import os
import pathlib
import sys

capture = {
    "args": sys.argv[1:],
    "env": {
        "GREWIA_REGEX_ENGINE": os.environ.get("GREWIA_REGEX_ENGINE"),
        "GREWIA_MATCH_MODE": os.environ.get("GREWIA_MATCH_MODE"),
        "GREWIA_ATTACK_STRING_LENGTH": os.environ.get("GREWIA_ATTACK_STRING_LENGTH"),
        "GREWIA_CANDIDATE_MODE": os.environ.get("GREWIA_CANDIDATE_MODE"),
        "GREWIA_DECREMENTAL": os.environ.get("GREWIA_DECREMENTAL"),
    },
}
pathlib.Path(os.environ["CAPTURE_PATH"]).write_text(json.dumps(capture), encoding="utf-8")
pathlib.Path(sys.argv[2]).write_text(json.dumps({
    "elapsed_ms": "42",
    "is_redos": False,
    "prefix": "",
    "infix": "",
    "suffix": "",
    "repeat_times": "-1"
}), encoding="utf-8")
output_dir = pathlib.Path(sys.argv[3])
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "10.txt").write_text("cccc", encoding="utf-8")
(output_dir / "2.txt").write_text("bb", encoding="utf-8")
(output_dir / "abc.txt").write_text("zzz", encoding="utf-8")
`);
    const capturePath = path.join(fixtureDir, 'capture.json');
    const result = runWrapper(fixtureDir, {
      env: { CAPTURE_PATH: capturePath }
    });
    const capture = JSON.parse(fs.readFileSync(capturePath, 'utf8'));

    assert.strictEqual(result.status, 0, result.stderr);
    assert.deepStrictEqual(capture.env, {
      GREWIA_REGEX_ENGINE: null,
      GREWIA_MATCH_MODE: null,
      GREWIA_ATTACK_STRING_LENGTH: null,
      GREWIA_CANDIDATE_MODE: null,
      GREWIA_DECREMENTAL: null
    });
    assert.strictEqual(capture.args[3], '100000');
    assert.strictEqual(capture.args[4], '1');
    assert.strictEqual(capture.args[5], '0');
    assert.strictEqual(capture.args[6], '1');
    assert.strictEqual(capture.args[7], 'Java');

    assert.deepStrictEqual(result.outputJson.toolMeta.normalizedOptions, {
      regexEngine: 'Java',
      matchMode: 0,
      attackStringLength: 100000,
      candidateMode: 'single',
      decremental: false
    });
    assert.strictEqual(result.outputJson.elapsed_ms, 42);
    assert.strictEqual(result.outputJson.is_redos, true);
    assert.strictEqual(result.outputJson.recommendedCandidateId, 'candidate-1');
    assert.deepStrictEqual(
      result.outputJson.candidates.map(candidate => candidate.metadata.sourceFile),
      ['2.txt', '10.txt', 'abc.txt']
    );
    assert.strictEqual(
      result.outputJson.candidates[0].attack.fullText,
      Buffer.from('bb', 'utf8').toString('base64')
    );
    assert.strictEqual(result.outputJson.candidates[0].payloadLength, 2);
    assert.strictEqual(result.outputJson.candidates[2].preview, 'zzz');
  });

  it('normalizes custom env options and maps them to GREWIA CLI arguments', () => {
    const fixtureDir = makeFixture(`
import json
import os
import pathlib
import sys

pathlib.Path(os.environ["CAPTURE_PATH"]).write_text(json.dumps({"args": sys.argv[1:]}), encoding="utf-8")
pathlib.Path(sys.argv[2]).write_text(json.dumps({
    "elapsed_ms": 8,
    "is_redos": True,
    "prefix": "",
    "infix": "",
    "suffix": "",
    "repeat_times": "5"
}), encoding="utf-8")
`);
    const capturePath = path.join(fixtureDir, 'capture.json');
    const result = runWrapper(fixtureDir, {
      env: {
        CAPTURE_PATH: capturePath,
        GREWIA_REGEX_ENGINE: 'Python',
        GREWIA_MATCH_MODE: '1',
        GREWIA_ATTACK_STRING_LENGTH: '4096',
        GREWIA_CANDIDATE_MODE: 'multiple',
        GREWIA_DECREMENTAL: 'yes'
      }
    });
    const capture = JSON.parse(fs.readFileSync(capturePath, 'utf8'));

    assert.strictEqual(result.status, 0, result.stderr);
    assert.strictEqual(capture.args[3], '4096');
    assert.strictEqual(capture.args[4], '0');
    assert.strictEqual(capture.args[5], '1');
    assert.strictEqual(capture.args[6], '0');
    assert.strictEqual(capture.args[7], 'Python');
    assert.deepStrictEqual(result.outputJson.toolMeta.normalizedOptions, {
      regexEngine: 'Python',
      matchMode: 1,
      attackStringLength: 4096,
      candidateMode: 'multiple',
      decremental: true
    });
    assert.strictEqual(result.outputJson.repeat_times, 5);
    assert.deepStrictEqual(result.outputJson.candidates, []);
  });

  it('falls back to safe defaults for invalid env values', () => {
    const fixtureDir = makeFixture(`
import json
import pathlib
import sys

pathlib.Path(sys.argv[2]).write_text(json.dumps({
    "elapsed_ms": 3,
    "is_redos": False
}), encoding="utf-8")
`);
    const result = runWrapper(fixtureDir, {
      env: {
        GREWIA_MATCH_MODE: 'not-a-number',
        GREWIA_ATTACK_STRING_LENGTH: '12',
        GREWIA_CANDIDATE_MODE: 'all',
        GREWIA_DECREMENTAL: 'on'
      }
    });

    assert.strictEqual(result.status, 0, result.stderr);
    assert.deepStrictEqual(result.outputJson.toolMeta.normalizedOptions, {
      regexEngine: 'Java',
      matchMode: 0,
      attackStringLength: 64,
      candidateMode: 'single',
      decremental: true
    });
  });

  it('fails clearly when the GREWIA executable is missing', () => {
    const fixtureDir = makeFixture(null);
    const result = runWrapper(fixtureDir);

    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /GREWIA executable not found/);
    assert.strictEqual(result.outputJson, null);
  });

  it('returns the underlying exit code when GREWIA fails without usable outputs', () => {
    const fixtureDir = makeFixture('import sys\nsys.exit(7)');
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 7);
    assert.match(result.stderr, /GREWIA failed with exit code 7/);
    assert.strictEqual(result.outputJson, null);
  });

  it('still normalizes output when GREWIA exits nonzero but leaves usable files behind', () => {
    const fixtureDir = makeFixture(`
import json
import pathlib
import sys

pathlib.Path(sys.argv[2]).write_text(json.dumps({
    "elapsed_ms": 9,
    "is_redos": False
}), encoding="utf-8")
output_dir = pathlib.Path(sys.argv[3])
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "1.txt").write_text("aaaaab", encoding="utf-8")
sys.exit(9)
`);
    const result = runWrapper(fixtureDir);

    assert.strictEqual(result.status, 0, result.stderr);
    assert.strictEqual(result.outputJson.is_redos, true);
    assert.strictEqual(result.outputJson.candidates.length, 1);
    assert.strictEqual(result.outputJson.toolMeta.candidateCount, 1);
  });

  it('reports a timeout instead of hanging indefinitely', () => {
    const fixtureDir = makeFixture(
      'import time\ntime.sleep(0.3)\n',
      {
        mutateRunPy(contents) {
          return contents.replace('timeout=300,', 'timeout=0.1,');
        }
      }
    );
    const result = runWrapper(fixtureDir);

    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /GREWIA execution timed out/);
    assert.strictEqual(result.outputJson, null);
  });
});
