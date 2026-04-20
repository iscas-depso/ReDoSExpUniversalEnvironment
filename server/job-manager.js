const { randomUUID } = require('crypto');

const JOB_TTL_MS = 30 * 60 * 1000;
const CLEANUP_INTERVAL_MS = 5 * 60 * 1000;
const MAX_JOBS = 1000;

function nowIso() {
  return new Date().toISOString();
}

function cloneWithoutListeners(job) {
  const { listeners, ...rest } = job;
  return JSON.parse(JSON.stringify(rest));
}

class JobManager {
  constructor(options = {}) {
    this.jobs = new Map();
    this.jobTtlMs = options.jobTtlMs || JOB_TTL_MS;
    this.maxJobs = options.maxJobs || MAX_JOBS;
    this.cleanupInterval = null;
    
    if (options.enableCleanup !== false) {
      this.startCleanup();
    }
  }

  startCleanup() {
    if (this.cleanupInterval) return;
    this.cleanupInterval = setInterval(() => this.cleanup(), CLEANUP_INTERVAL_MS);
    this.cleanupInterval.unref();
  }

  stopCleanup() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }

  cleanup() {
    const now = Date.now();
    const terminalStatuses = ['completed', 'completed_with_errors', 'failed', 'cancelled'];
    
    for (const [id, job] of this.jobs) {
      if (!terminalStatuses.includes(job.status)) continue;
      if (job.listeners && job.listeners.size > 0) continue;
      
      const updatedAt = new Date(job.updatedAt).getTime();
      if (now - updatedAt > this.jobTtlMs) {
        this.jobs.delete(id);
      }
    }
    
    if (this.jobs.size > this.maxJobs) {
      const sorted = [...this.jobs.entries()]
        .filter(([, j]) => terminalStatuses.includes(j.status) && (!j.listeners || j.listeners.size === 0))
        .sort((a, b) => new Date(a[1].updatedAt) - new Date(b[1].updatedAt));
      
      const toRemove = this.jobs.size - this.maxJobs;
      for (let i = 0; i < Math.min(toRemove, sorted.length); i++) {
        this.jobs.delete(sorted[i][0]);
      }
    }
  }

  createJob({ type, items = [], request = {}, metadata = {} }) {
    const id = randomUUID();
    const job = {
      id,
      type,
      status: 'queued',
      createdAt: nowIso(),
      updatedAt: nowIso(),
      request,
      metadata,
      progress: {
        total: items.length,
        completed: 0
      },
      results: items.map(item => ({
        id: item.id,
        label: item.label,
        description: item.description || '',
        status: 'pending',
        startedAt: null,
        finishedAt: null,
        elapsedMs: null,
        output: null,
        error: null,
        logs: []
      })),
      error: null,
      listeners: new Set()
    };
    this.jobs.set(id, job);
    return job;
  }

  getJob(jobId) {
    return this.jobs.get(jobId) || null;
  }

  serialize(job) {
    return cloneWithoutListeners(job);
  }

  subscribe(jobId, res) {
    const job = this.jobs.get(jobId);
    if (!job) {
      return null;
    }

    job.listeners.add(res);

    const heartbeat = setInterval(() => {
      res.write(': heartbeat\n\n');
      if (typeof res.flush === 'function') {
        res.flush();
      }
    }, 15000);
    heartbeat.unref?.();

    res.on('close', () => {
      clearInterval(heartbeat);
      job.listeners.delete(res);
    });

    res.on('error', () => {
      clearInterval(heartbeat);
      job.listeners.delete(res);
    });

    return job;
  }

  broadcast(job) {
    const payload = this.serialize(job);
    const data = `data: ${JSON.stringify(payload)}\n\n`;
    for (const listener of job.listeners) {
      listener.write(data);
      if (typeof listener.flush === 'function') {
        listener.flush();
      }
    }
  }

  updateJob(job, updates = {}) {
    Object.assign(job, updates);
    job.updatedAt = nowIso();
    this.broadcast(job);
  }

  updateResult(job, resultId, updater) {
    const target = job.results.find(r => r.id === resultId);
    if (!target) {
      return null;
    }
    updater(target);
    job.updatedAt = nowIso();
    this.broadcast(job);
    return target;
  }

  incrementProgress(job) {
    job.progress.completed = Math.min(job.progress.completed + 1, job.progress.total);
    job.updatedAt = nowIso();
    this.broadcast(job);
  }

  finalizeJob(job, status, error = null) {
    job.status = status;
    job.error = error ? String(error.message || error) : null;
    job.updatedAt = nowIso();
    this.broadcast(job);
  }
}

module.exports = JobManager;
