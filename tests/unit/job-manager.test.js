const { describe, it, beforeEach, after } = require('node:test');
const assert = require('node:assert');
const JobManager = require('../../server/job-manager');

describe('JobManager', () => {
  let jobManager;

  beforeEach(() => {
    jobManager = new JobManager({ enableCleanup: false });
  });

  after(() => {
    if (jobManager) {
      jobManager.stopCleanup();
    }
  });

  describe('createJob', () => {
    it('creates a job with unique id and correct initial state', () => {
      const job = jobManager.createJob({
        type: 'tools',
        items: [{ id: 'regexploit', label: 'RegExploit' }],
        request: { regexLength: 10 }
      });

      assert.ok(job.id);
      assert.strictEqual(job.type, 'tools');
      assert.strictEqual(job.status, 'queued');
      assert.strictEqual(job.progress.total, 1);
      assert.strictEqual(job.progress.completed, 0);
      assert.strictEqual(job.results.length, 1);
      assert.strictEqual(job.results[0].id, 'regexploit');
      assert.strictEqual(job.results[0].status, 'pending');
    });

    it('creates jobs with unique ids', () => {
      const job1 = jobManager.createJob({ type: 'tools', items: [] });
      const job2 = jobManager.createJob({ type: 'tools', items: [] });
      
      assert.notStrictEqual(job1.id, job2.id);
    });

    it('stores job in internal map', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      
      assert.strictEqual(jobManager.getJob(job.id), job);
    });
  });

  describe('getJob', () => {
    it('returns null for non-existent job', () => {
      assert.strictEqual(jobManager.getJob('non-existent-id'), null);
    });

    it('returns job for valid id', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      const retrieved = jobManager.getJob(job.id);
      
      assert.strictEqual(retrieved.id, job.id);
    });
  });

  describe('serialize', () => {
    it('returns job without listeners set', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      const serialized = jobManager.serialize(job);
      
      assert.strictEqual(serialized.listeners, undefined);
      assert.strictEqual(serialized.id, job.id);
    });

    it('creates a deep copy', () => {
      const job = jobManager.createJob({ type: 'tools', items: [{ id: 'test' }] });
      const serialized = jobManager.serialize(job);
      
      serialized.status = 'modified';
      assert.strictEqual(job.status, 'queued');
    });
  });

  describe('updateJob', () => {
    it('updates job properties', async () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      const originalUpdatedAt = job.updatedAt;
      
      await new Promise(r => setTimeout(r, 5));
      
      jobManager.updateJob(job, { status: 'running' });
      
      assert.strictEqual(job.status, 'running');
      assert.ok(new Date(job.updatedAt) >= new Date(originalUpdatedAt));
    });
  });

  describe('updateResult', () => {
    it('updates specific result within job', () => {
      const job = jobManager.createJob({
        type: 'tools',
        items: [
          { id: 'tool1', label: 'Tool 1' },
          { id: 'tool2', label: 'Tool 2' }
        ]
      });
      
      jobManager.updateResult(job, 'tool1', result => {
        result.status = 'running';
        result.startedAt = new Date().toISOString();
      });
      
      assert.strictEqual(job.results[0].status, 'running');
      assert.strictEqual(job.results[1].status, 'pending');
    });

    it('returns null for non-existent result', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      const result = jobManager.updateResult(job, 'non-existent', () => {});
      
      assert.strictEqual(result, null);
    });
  });

  describe('incrementProgress', () => {
    it('increments completed count', () => {
      const job = jobManager.createJob({
        type: 'tools',
        items: [{ id: 'tool1' }, { id: 'tool2' }]
      });
      
      assert.strictEqual(job.progress.completed, 0);
      
      jobManager.incrementProgress(job);
      assert.strictEqual(job.progress.completed, 1);
      
      jobManager.incrementProgress(job);
      assert.strictEqual(job.progress.completed, 2);
    });

    it('does not exceed total', () => {
      const job = jobManager.createJob({
        type: 'tools',
        items: [{ id: 'tool1' }]
      });
      
      jobManager.incrementProgress(job);
      jobManager.incrementProgress(job);
      jobManager.incrementProgress(job);
      
      assert.strictEqual(job.progress.completed, 1);
    });
  });

  describe('finalizeJob', () => {
    it('sets final status', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      
      jobManager.finalizeJob(job, 'completed');
      
      assert.strictEqual(job.status, 'completed');
      assert.strictEqual(job.error, null);
    });

    it('sets error message when provided', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      
      jobManager.finalizeJob(job, 'failed', new Error('Test error'));
      
      assert.strictEqual(job.status, 'failed');
      assert.strictEqual(job.error, 'Test error');
    });
  });

  describe('cleanup', () => {
    it('removes old completed jobs', () => {
      const manager = new JobManager({ 
        enableCleanup: false, 
        jobTtlMs: 100 
      });
      
      const job = manager.createJob({ type: 'tools', items: [] });
      manager.finalizeJob(job, 'completed');
      
      job.updatedAt = new Date(Date.now() - 200).toISOString();
      
      manager.cleanup();
      
      assert.strictEqual(manager.getJob(job.id), null);
    });

    it('keeps jobs with active listeners', () => {
      const manager = new JobManager({ 
        enableCleanup: false, 
        jobTtlMs: 100 
      });
      
      const job = manager.createJob({ type: 'tools', items: [] });
      manager.finalizeJob(job, 'completed');
      job.updatedAt = new Date(Date.now() - 200).toISOString();
      job.listeners.add({ write: () => {} });
      
      manager.cleanup();
      
      assert.ok(manager.getJob(job.id));
    });

    it('keeps running jobs', () => {
      const manager = new JobManager({ 
        enableCleanup: false, 
        jobTtlMs: 100 
      });
      
      const job = manager.createJob({ type: 'tools', items: [] });
      manager.updateJob(job, { status: 'running' });
      job.updatedAt = new Date(Date.now() - 200).toISOString();
      
      manager.cleanup();
      
      assert.ok(manager.getJob(job.id));
    });

    it('enforces max jobs limit', () => {
      const manager = new JobManager({ 
        enableCleanup: false, 
        maxJobs: 2 
      });
      
      const job1 = manager.createJob({ type: 'tools', items: [] });
      const job2 = manager.createJob({ type: 'tools', items: [] });
      const job3 = manager.createJob({ type: 'tools', items: [] });
      
      manager.finalizeJob(job1, 'completed');
      manager.finalizeJob(job2, 'completed');
      manager.finalizeJob(job3, 'completed');
      
      job1.updatedAt = new Date(Date.now() - 1000).toISOString();
      job2.updatedAt = new Date(Date.now() - 500).toISOString();
      
      manager.cleanup();
      
      assert.strictEqual(manager.getJob(job1.id), null);
      assert.ok(manager.getJob(job2.id));
      assert.ok(manager.getJob(job3.id));
    });
  });

  describe('subscribe', () => {
    it('returns null for non-existent job', () => {
      const result = jobManager.subscribe('non-existent', {});
      assert.strictEqual(result, null);
    });

    it('adds response to listeners', () => {
      const job = jobManager.createJob({ type: 'tools', items: [] });
      const mockRes = {
        on: () => {},
        write: () => {}
      };
      
      jobManager.subscribe(job.id, mockRes);
      
      assert.strictEqual(job.listeners.size, 1);
    });
  });
});
