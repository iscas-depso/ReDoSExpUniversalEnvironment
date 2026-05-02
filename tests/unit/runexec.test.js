const { afterEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

const {
  cleanupStaleBenchExecCgroups,
  computeExecTimeoutMs,
  parseRunexecStreams,
  parseRunexecStreamsWithOutputLog
} = require('../../server/runexec');

const TEMP_DIRS = [];

async function makeCgroupTree(rootPath, name, { populated = '0', procs = '', threads = '', children = [] } = {}) {
  const dirPath = path.join(rootPath, name);
  await fs.mkdir(dirPath, { recursive: true });
  await fs.writeFile(path.join(dirPath, 'cgroup.events'), `populated ${populated}\nfrozen 0\n`, 'utf8');
  await fs.writeFile(path.join(dirPath, 'cgroup.procs'), procs, 'utf8');
  await fs.writeFile(path.join(dirPath, 'cgroup.threads'), threads, 'utf8');
  for (const child of children) {
    await makeCgroupTree(dirPath, child.name, child);
  }
  return dirPath;
}

afterEach(async () => {
  await Promise.all(TEMP_DIRS.splice(0).map(dirPath => fs.rm(dirPath, { recursive: true, force: true })));
});

describe('runexec cgroup cleanup', () => {
  it('parses runexec metrics from combined stdout and stderr streams', () => {
    const parsed = parseRunexecStreams(
      '2015-03-06 12:54:01,707 - INFO - Starting command echo Test\nreturnvalue=0\n',
      'walltime=0.0024175643920898438s\ncputime=0.001671s\nmemory=131072\n'
    );

    assert.strictEqual(parsed.returnValue, 0);
    assert.strictEqual(parsed.terminationReason, null);
    assert.strictEqual(parsed.walltime, '0.0024175643920898438s');
    assert.strictEqual(parsed.cputime, '0.001671s');
    assert.strictEqual(parsed.memory, '131072');
  });

  it('parses runexec metrics from the output log when stdout/stderr omit the summary', async () => {
    const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'runexec-output-log-test-'));
    TEMP_DIRS.push(tempDir);
    const outputLogPath = path.join(tempDir, 'output.log');
    await fs.writeFile(
      outputLogPath,
      'program output\nreturnvalue=0\nwalltime=1.5s\ncputime=1.2s\nmemory=4096\n',
      'utf8'
    );

    const { parsed, outputLog } = await parseRunexecStreamsWithOutputLog('', '', outputLogPath);

    assert.strictEqual(parsed.returnValue, 0);
    assert.strictEqual(parsed.walltime, '1.5s');
    assert.strictEqual(parsed.cputime, '1.2s');
    assert.strictEqual(parsed.memory, '4096');
    assert.match(outputLog, /program output/);
  });

  it('gives BenchExec enough extra time to flush summaries after walltime expiry', () => {
    assert.strictEqual(computeExecTimeoutMs(undefined), undefined);
    assert.strictEqual(computeExecTimeoutMs(615), 1_215_000);
  });

  it('removes stale BenchExec cgroup trees and keeps populated ones', async () => {
    const rootPath = await fs.mkdtemp(path.join(os.tmpdir(), 'runexec-cgroup-test-'));
    TEMP_DIRS.push(rootPath);

    const staleDir = await makeCgroupTree(rootPath, 'benchexec_stale', {
      populated: '0',
      children: [
        {
          name: 'benchexec_process_dead',
          populated: '0'
        }
      ]
    });
    const liveDir = await makeCgroupTree(rootPath, 'benchexec_live', {
      populated: '1',
      procs: '123\n',
      children: [
        {
          name: 'benchexec_process_live',
          populated: '1',
          procs: '456\n'
        }
      ]
    });

    const result = await cleanupStaleBenchExecCgroups({ force: true, rootPath, allowFileCleanup: true, minAgeMs: 0 });

    await assert.rejects(fs.stat(staleDir), /ENOENT/);
    await fs.stat(liveDir);
    assert.ok(result.removed >= 2);
    assert.strictEqual(result.remaining, 1);
  });

  it('ignores transient ENODEV errors while cleaning stale cgroups', async () => {
    const rootPath = await fs.mkdtemp(path.join(os.tmpdir(), 'runexec-cgroup-test-'));
    TEMP_DIRS.push(rootPath);

    const staleDir = await makeCgroupTree(rootPath, 'benchexec_stale_enodev', {
      populated: '0'
    });

    const originalReadFile = fs.readFile;
    fs.readFile = async (targetPath, ...args) => {
      if (String(targetPath).includes('benchexec_stale_enodev') && String(targetPath).endsWith('cgroup.procs')) {
        const error = new Error('no such device, read');
        error.code = 'ENODEV';
        throw error;
      }
      return originalReadFile(targetPath, ...args);
    };

    try {
      const result = await cleanupStaleBenchExecCgroups({ force: true, rootPath, allowFileCleanup: true, minAgeMs: 0 });
      await assert.rejects(fs.stat(staleDir), /ENOENT/);
      assert.strictEqual(result.remaining, 0);
    } finally {
      fs.readFile = originalReadFile;
    }
  });

  it('does not remove fresh BenchExec cgroups that may still be initializing', async () => {
    const rootPath = await fs.mkdtemp(path.join(os.tmpdir(), 'runexec-cgroup-test-'));
    TEMP_DIRS.push(rootPath);

    const staleDir = await makeCgroupTree(rootPath, 'benchexec_old', { populated: '0' });
    const freshDir = await makeCgroupTree(rootPath, 'benchexec_fresh', { populated: '0' });

    const oldTimestamp = new Date(Date.now() - 120_000);
    await fs.utimes(staleDir, oldTimestamp, oldTimestamp);

    const result = await cleanupStaleBenchExecCgroups({
      force: true,
      rootPath,
      allowFileCleanup: true,
      minAgeMs: 60_000
    });

    await assert.rejects(fs.stat(staleDir), /ENOENT/);
    await fs.stat(freshDir);
    assert.strictEqual(result.remaining, 1);
  });
});
