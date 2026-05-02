const fs = require('fs');
const os = require('os');

function parseCpuSetSpec(value) {
  if (!value) {
    return [];
  }

  const cpuIds = new Set();
  for (const rawPart of String(value).trim().split(',')) {
    const part = rawPart.trim();
    if (!part) {
      continue;
    }
    const rangeMatch = part.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) {
      const start = Number(rangeMatch[1]);
      const end = Number(rangeMatch[2]);
      if (Number.isInteger(start) && Number.isInteger(end) && start <= end) {
        for (let current = start; current <= end; current += 1) {
          cpuIds.add(current);
        }
      }
      continue;
    }

    const cpuId = Number(part);
    if (Number.isInteger(cpuId) && cpuId >= 0) {
      cpuIds.add(cpuId);
    }
  }

  return Array.from(cpuIds).sort((a, b) => a - b);
}

function readVisibleCpuSpecFromProcStatus() {
  try {
    const status = fs.readFileSync('/proc/self/status', 'utf8');
    const line = status.split(/\r?\n/).find(entry => entry.startsWith('Cpus_allowed_list:'));
    if (!line) {
      return '';
    }
    return line.split(':')[1]?.trim() || '';
  } catch {
    return '';
  }
}

function detectVisibleCpuIds() {
  const override = process.env.CPU_ALLOCATOR_VISIBLE_CORES || process.env.BATCH_VISIBLE_CPU_IDS;
  const overrideIds = parseCpuSetSpec(override);
  if (overrideIds.length > 0) {
    return overrideIds;
  }

  const procStatusIds = parseCpuSetSpec(readVisibleCpuSpecFromProcStatus());
  if (procStatusIds.length > 0) {
    return procStatusIds;
  }

  try {
    const cpusetIds = parseCpuSetSpec(fs.readFileSync('/sys/fs/cgroup/cpuset.cpus.effective', 'utf8'));
    if (cpusetIds.length > 0) {
      return cpusetIds;
    }
  } catch {
    // ignore and fall back
  }

  return Array.from({ length: os.cpus().length }, (_, i) => i);
}

class CpuAllocator {
  constructor(totalCoresOrVisibleCpuIds) {
    if (Array.isArray(totalCoresOrVisibleCpuIds) && totalCoresOrVisibleCpuIds.length > 0) {
      this.visibleCpuIds = [...new Set(totalCoresOrVisibleCpuIds)]
        .filter(value => Number.isInteger(value) && value >= 0)
        .sort((a, b) => a - b);
    } else if (Number.isFinite(totalCoresOrVisibleCpuIds) && totalCoresOrVisibleCpuIds > 0) {
      this.visibleCpuIds = Array.from({ length: totalCoresOrVisibleCpuIds }, (_, i) => i);
    } else {
      this.visibleCpuIds = detectVisibleCpuIds();
    }

    this.totalCores = this.visibleCpuIds.length;
    this.free = new Set(this.visibleCpuIds);
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
    if (!Number.isFinite(count) || count <= 0) {
      return Promise.resolve({
        cores: [],
        release: () => {}
      });
    }
    if (count > this.totalCores) {
      return Promise.reject(new Error(`Requested ${count} CPU cores, but only ${this.totalCores} are visible in this container.`));
    }
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
  coresToSpec,
  parseCpuSetSpec,
  detectVisibleCpuIds
};
