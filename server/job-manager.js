const { randomUUID } = require('crypto');

function nowIso() {
  return new Date().toISOString();
}

function cloneWithoutListeners(job) {
  const { listeners, ...rest } = job;
  return JSON.parse(JSON.stringify(rest));
}

class JobManager {
  constructor() {
    this.jobs = new Map();
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
