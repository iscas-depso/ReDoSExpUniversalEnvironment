const { describe, it, beforeEach } = require('node:test');
const assert = require('node:assert');
const { CpuAllocator, coresToSpec } = require('../../server/cpu-allocator');

describe('CpuAllocator', () => {
  describe('constructor', () => {
    it('defaults to system CPU count', () => {
      const os = require('os');
      const allocator = new CpuAllocator();
      assert.strictEqual(allocator.totalCores, os.cpus().length);
    });

    it('accepts custom core count', () => {
      const allocator = new CpuAllocator(4);
      assert.strictEqual(allocator.totalCores, 4);
    });

    it('initializes all cores as free', () => {
      const allocator = new CpuAllocator(4);
      assert.strictEqual(allocator.getFreeCount(), 4);
    });
  });

  describe('acquire', () => {
    it('allocates requested number of cores', async () => {
      const allocator = new CpuAllocator(4);
      const allocation = await allocator.acquire(2);
      
      assert.strictEqual(allocation.cores.length, 2);
      assert.strictEqual(allocator.getFreeCount(), 2);
    });

    it('prefers contiguous core blocks', async () => {
      const allocator = new CpuAllocator(8);
      const allocation = await allocator.acquire(3);
      
      const cores = allocation.cores;
      for (let i = 1; i < cores.length; i++) {
        assert.strictEqual(cores[i], cores[i - 1] + 1);
      }
    });

    it('provides release function', async () => {
      const allocator = new CpuAllocator(4);
      const allocation = await allocator.acquire(2);
      
      assert.strictEqual(allocator.getFreeCount(), 2);
      
      allocation.release();
      
      assert.strictEqual(allocator.getFreeCount(), 4);
    });

    it('queues requests when not enough cores available', async () => {
      const allocator = new CpuAllocator(2);
      
      const alloc1 = await allocator.acquire(2);
      
      let alloc2Resolved = false;
      const alloc2Promise = allocator.acquire(2).then(a => {
        alloc2Resolved = true;
        return a;
      });
      
      await new Promise(r => setTimeout(r, 10));
      assert.strictEqual(alloc2Resolved, false);
      
      alloc1.release();
      
      const alloc2 = await alloc2Promise;
      assert.strictEqual(alloc2Resolved, true);
      assert.strictEqual(alloc2.cores.length, 2);
    });
  });

  describe('release', () => {
    it('returns cores to the pool', async () => {
      const allocator = new CpuAllocator(4);
      const allocation = await allocator.acquire(4);
      
      assert.strictEqual(allocator.getFreeCount(), 0);
      
      allocator.release(allocation.cores);
      
      assert.strictEqual(allocator.getFreeCount(), 4);
    });

    it('handles empty or null input gracefully', () => {
      const allocator = new CpuAllocator(4);
      
      allocator.release(null);
      allocator.release([]);
      allocator.release(undefined);
      
      assert.strictEqual(allocator.getFreeCount(), 4);
    });
  });
});

describe('coresToSpec', () => {
  it('returns empty string for empty array', () => {
    assert.strictEqual(coresToSpec([]), '');
  });

  it('returns empty string for null/undefined', () => {
    assert.strictEqual(coresToSpec(null), '');
    assert.strictEqual(coresToSpec(undefined), '');
  });

  it('handles single core', () => {
    assert.strictEqual(coresToSpec([0]), '0');
    assert.strictEqual(coresToSpec([5]), '5');
  });

  it('creates ranges for contiguous cores', () => {
    assert.strictEqual(coresToSpec([0, 1, 2, 3]), '0-3');
    assert.strictEqual(coresToSpec([2, 3, 4]), '2-4');
  });

  it('handles non-contiguous cores', () => {
    assert.strictEqual(coresToSpec([0, 2, 4]), '0,2,4');
  });

  it('combines ranges and individual cores', () => {
    assert.strictEqual(coresToSpec([0, 1, 2, 5, 7, 8, 9]), '0-2,5,7-9');
  });

  it('handles unsorted input', () => {
    assert.strictEqual(coresToSpec([3, 1, 2, 0]), '0-3');
  });

  it('handles duplicates', () => {
    assert.strictEqual(coresToSpec([0, 0, 1, 1, 2]), '0-2');
  });
});
