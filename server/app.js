const path = require('path');

const compression = require('compression');
const express = require('express');
const morgan = require('morgan');

const JobManager = require('./job-manager');
const { CpuAllocator } = require('./cpu-allocator');
const {
  TOOL_DEFINITIONS,
  TOOL_METADATA,
  ENGINE_DEFINITIONS,
  ENGINE_METADATA,
  MATCH_MODES,
  DEFAULT_OPTIONS,
  normalizeToolOptions
} = require('./definitions');
const { runToolsJob } = require('./tool-runner');
const { runEnginesJob } = require('./engine-runner');

function sanitizeRegexInput(value) {
  if (typeof value !== 'string') {
    return '';
  }
  return value.trim();
}

function normalizeIdList(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return [...new Set(value.map(item => String(item).trim()).filter(Boolean))];
}

function createApp(options = {}) {
  const {
    jobManager: providedJobManager,
    runTools = runToolsJob,
    runEngines = runEnginesJob,
    logError = console.error
  } = options;

  const jobManager = providedJobManager || new JobManager();
  const cpuAllocator = new CpuAllocator();
  const app = express();

  app.locals.jobManager = jobManager;
  app.locals.cpuAllocator = cpuAllocator;

  app.disable('x-powered-by');
  app.use(compression());
  app.use(express.json({ limit: '1mb' }));
  app.use(
    morgan('dev', {
      skip: () => process.env.NODE_ENV === 'test'
    })
  );

  app.get('/api/meta', (req, res) => {
    res.json({
      tools: TOOL_METADATA,
      engines: ENGINE_METADATA,
      matchModes: MATCH_MODES,
      defaults: {
        toolTimeoutSeconds: Math.round(DEFAULT_OPTIONS.toolTimeoutMs / 1000),
        engineTimeoutSeconds: Math.round(DEFAULT_OPTIONS.engineTimeoutMs / 1000),
        maxRepeatTimes: DEFAULT_OPTIONS.maxRepeatTimes,
        maxAttackLength: DEFAULT_OPTIONS.maxAttackLength,
        defaultCores: DEFAULT_OPTIONS.defaultCores || null,
        defaultMemoryMB: DEFAULT_OPTIONS.defaultMemoryMB || null
      },
      runtime: {
        visibleCpuIds: cpuAllocator.visibleCpuIds,
        visibleCpuCount: cpuAllocator.totalCores
      }
    });
  });

  app.get('/api/jobs/:id', (req, res) => {
    const job = jobManager.getJob(req.params.id);
    if (!job) {
      res.status(404).json({ error: 'Job not found' });
      return;
    }
    res.json(jobManager.serialize(job));
  });

  app.get('/api/jobs/:id/stream', (req, res) => {
    const job = jobManager.getJob(req.params.id);
    if (!job) {
      res.status(404).json({ error: 'Job not found' });
      return;
    }

    res.set({
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    });
    res.flushHeaders?.();

  jobManager.subscribe(job.id, res);
  res.write(`data: ${JSON.stringify(jobManager.serialize(job))}\n\n`);
  res.flush?.();
});

  app.post('/api/jobs/tools', (req, res) => {
    const regex = sanitizeRegexInput(req.body?.regex);
    const toolIds = normalizeIdList(req.body?.tools);
    const rawToolOptions = req.body?.toolOptions;

    if (!regex) {
      res.status(400).json({ error: 'Regex input is required.' });
      return;
    }

    if (!toolIds.length) {
      res.status(400).json({ error: 'At least one tool must be selected.' });
      return;
    }

    const invalidTools = toolIds.filter(id => !TOOL_DEFINITIONS[id]);
    if (invalidTools.length) {
      res.status(400).json({ error: `Unsupported tools requested: ${invalidTools.join(', ')}` });
      return;
    }

    if (rawToolOptions !== undefined && (typeof rawToolOptions !== 'object' || Array.isArray(rawToolOptions) || rawToolOptions === null)) {
      res.status(400).json({ error: 'toolOptions must be an object keyed by tool id.' });
      return;
    }

    const toolOptions = {};
    try {
      for (const toolId of toolIds) {
        toolOptions[toolId] = normalizeToolOptions(toolId, rawToolOptions?.[toolId]);
      }
    } catch (error) {
      res.status(400).json({ error: error.message || 'Invalid toolOptions provided.' });
      return;
    }

    const timeoutSeconds = Number(req.body?.timeoutSeconds);
    const cpuCores = Number(req.body?.cpuCores);
    const memoryMB = Number(req.body?.memoryMB);
    if (Number.isFinite(cpuCores) && cpuCores > cpuAllocator.totalCores) {
      res.status(400).json({
        error: `Requested ${cpuCores} CPU cores, but only ${cpuAllocator.totalCores} are visible inside this container.`
      });
      return;
    }
    const timeoutMs = Number.isFinite(timeoutSeconds) && timeoutSeconds > 0
      ? Math.min(timeoutSeconds, 3600) * 1000
      : undefined;

    const items = toolIds.map(id => ({
      id,
      label: TOOL_DEFINITIONS[id].label,
      description: TOOL_DEFINITIONS[id].description
    }));

    const job = jobManager.createJob({
      type: 'tools',
      items,
      request: {
        regexLength: regex.length,
        toolIds,
        toolOptions,
        timeoutMs: timeoutMs || DEFAULT_OPTIONS.toolTimeoutMs,
        cpuCores: Number.isFinite(cpuCores) && cpuCores > 0 ? cpuCores : (DEFAULT_OPTIONS.defaultCores || null),
        memoryMB: Number.isFinite(memoryMB) && memoryMB > 0 ? memoryMB : (DEFAULT_OPTIONS.defaultMemoryMB || null)
      }
    });

    res.status(202).json({
      jobId: job.id,
      status: job.status
    });

    setImmediate(async () => {
      try {
        await runTools(jobManager, job, {
          regex,
          toolIds,
          toolOptions,
          timeoutMs,
          cpuAllocator,
          cpuCores: Number.isFinite(cpuCores) && cpuCores > 0 ? cpuCores : undefined,
          memoryMB: Number.isFinite(memoryMB) && memoryMB > 0 ? memoryMB : undefined
        });
      } catch (error) {
        logError('Tool job failed:', error);
        jobManager.finalizeJob(job, 'failed', error);
      }
    });
  });

  app.post('/api/jobs/engines', (req, res) => {
    const regex = sanitizeRegexInput(req.body?.regex);
    const engines = normalizeIdList(req.body?.engines);
    const matchModeRaw = Number(req.body?.matchMode ?? 0);
    const repeatOverride = Number(req.body?.repeatOverride);
    const maxAttackLength = Number(req.body?.maxAttackLength);
    const maxRepeatTimes = Number(req.body?.maxRepeatTimes);
    const timeoutSeconds = Number(req.body?.timeoutSeconds);
    const attack = req.body?.attack;
    const cpuCores = Number(req.body?.cpuCores);
    const memoryMB = Number(req.body?.memoryMB);
    const attackSource = req.body?.attackSource || {};
    if (Number.isFinite(cpuCores) && cpuCores > cpuAllocator.totalCores) {
      res.status(400).json({
        error: `Requested ${cpuCores} CPU cores, but only ${cpuAllocator.totalCores} are visible inside this container.`
      });
      return;
    }

    if (!regex) {
      res.status(400).json({ error: 'Regex input is required.' });
      return;
    }

    if (!Array.isArray(engines) || !engines.length) {
      res.status(400).json({ error: 'At least one engine must be selected.' });
      return;
    }

    if (!attack || typeof attack !== 'object') {
      res.status(400).json({ error: 'Attack data from a tool result is required.' });
      return;
    }

    const invalidEngines = engines.filter(id => !ENGINE_DEFINITIONS[id]);
    if (invalidEngines.length) {
      res.status(400).json({ error: `Unsupported engines requested: ${invalidEngines.join(', ')}` });
      return;
    }

    const timeoutMs = Number.isFinite(timeoutSeconds) && timeoutSeconds > 0
      ? Math.min(timeoutSeconds, 3600) * 1000
      : undefined;

    const matchMode = matchModeRaw === 1 ? 1 : 0;

    const items = engines.map(id => ({
      id,
      label: ENGINE_DEFINITIONS[id].label,
      description: ENGINE_DEFINITIONS[id].description
    }));

    const job = jobManager.createJob({
      type: 'engines',
      items,
      request: {
        regexLength: regex.length,
        engineIds: engines,
        matchMode,
        repeatOverride: Number.isFinite(repeatOverride) ? repeatOverride : null,
        timeoutMs: timeoutMs || DEFAULT_OPTIONS.engineTimeoutMs,
        cpuCores: Number.isFinite(cpuCores) && cpuCores > 0 ? cpuCores : (DEFAULT_OPTIONS.defaultCores || null),
        memoryMB: Number.isFinite(memoryMB) && memoryMB > 0 ? memoryMB : (DEFAULT_OPTIONS.defaultMemoryMB || null),
        attackSource
      }
    });

    res.status(202).json({
      jobId: job.id,
      status: job.status
    });

    setImmediate(async () => {
      try {
        await runEngines(jobManager, job, {
          regex,
          engines,
          attack,
          attackSource,
          matchMode,
          timeoutMs,
          cpuAllocator,
          cpuCores: Number.isFinite(cpuCores) && cpuCores > 0 ? cpuCores : undefined,
          memoryMB: Number.isFinite(memoryMB) && memoryMB > 0 ? memoryMB : undefined,
          repeatOverride: Number.isFinite(repeatOverride) ? repeatOverride : undefined,
          maxAttackLength: Number.isFinite(maxAttackLength) && maxAttackLength > 0 ? maxAttackLength : undefined,
          maxRepeatTimes: Number.isFinite(maxRepeatTimes) && maxRepeatTimes > 0 ? maxRepeatTimes : undefined
        });
      } catch (error) {
        logError('Engine job failed:', error);
        jobManager.finalizeJob(job, 'failed', error);
      }
    });
  });

  const publicDir = path.join(__dirname, '..', 'public');
  app.use(express.static(publicDir, { fallthrough: true }));

  app.use((req, res, next) => {
    if (req.path.startsWith('/api/')) {
      res.status(404).json({ error: 'API route not found' });
      return;
    }
    next();
  });

  app.get('*', (req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
  });

  return app;
}

module.exports = {
  createApp
};
