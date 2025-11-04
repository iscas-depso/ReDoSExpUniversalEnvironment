const os = require('os');

class CpuAllocator {
  constructor(totalCores) {
    this.totalCores = Number.isFinite(totalCores) && totalCores > 0 ? totalCores : os.cpus().length;
    this.free = new Set(Array.from({ length: this.totalCores }, (_, i) => i));
    this.queue = [];
  }

  getFreeCount() {
    return this.free.size;
  }

  // Try to allocate a set of cores immediately, prefer contiguous ranges.
  _tryAllocate(count) {
    if (!Number.isFinite(count) || count <= 0) {
      return [];
    }
    if (count > this.free.size) {
      return null;
    }

    const freeSorted = Array.from(this.free).sort((a, b) => a - b);
    // Try contiguous block first
    let startIdx = 0;
    while (startIdx < freeSorted.length) {
      const start = freeSorted[startIdx];
      let len = 1;
      let idx = startIdx + 1;
      while (idx < freeSorted.length && freeSorted[idx] === freeSorted[idx - 1] + 1 && len < count) {
        len += 1;
        idx += 1;
      }
      if (len >= count) {
        const allocated = [];
        for (let i = start; i < start + count; i += 1) {
          allocated.push(i);
        }
        allocated.forEach(c => this.free.delete(c));
        return allocated;
      }
      startIdx = idx;
    }

    // Fallback: pick first N free cores (non-contiguous)
    const allocated = freeSorted.slice(0, count);
    allocated.forEach(c => this.free.delete(c));
    return allocated;
  }

  acquire(count) {
    return new Promise(resolve => {
      const tryNow = () => {
        const cores = this._tryAllocate(count);
        if (cores && cores.length === count) {
          resolve({
            cores,
            release: () => this.release(cores)
          });
          return true;
        }
        return false;
      };

      if (tryNow()) return;

      // Enqueue request
      const request = { count, resolve, cancelled: false };
      this.queue.push(request);
    });
  }

  release(cores) {
    if (!cores || !cores.length) return;
    cores.forEach(c => this.free.add(c));
    this._drainQueue();
  }

  _drainQueue() {
    if (!this.queue.length) return;
    // FIFO fairness
    let progressed = true;
    while (progressed) {
      progressed = false;
      for (let i = 0; i < this.queue.length; i += 1) {
        const req = this.queue[i];
        if (req.cancelled) continue;
        const cores = this._tryAllocate(req.count);
        if (cores && cores.length === req.count) {
          this.queue.splice(i, 1);
          req.resolve({
            cores,
            release: () => this.release(cores)
          });
          progressed = true;
          break;
        }
      }
    }
  }
}

function coresToSpec(cores) {
  if (!cores || cores.length === 0) return '';
  const sorted = [...new Set(cores)].sort((a, b) => a - b);
  const ranges = [];
  let start = sorted[0];
  let prev = start;
  for (let i = 1; i < sorted.length; i += 1) {
    const cur = sorted[i];
    if (cur === prev + 1) {
      prev = cur;
      continue;
    }
    ranges.push(start === prev ? `${start}` : `${start}-${prev}`);
    start = prev = cur;
  }
  ranges.push(start === prev ? `${start}` : `${start}-${prev}`);
  return ranges.join(',');
}

module.exports = {
  CpuAllocator,
  coresToSpec
};

