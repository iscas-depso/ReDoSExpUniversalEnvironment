const path = require('path');

const compression = require('compression');
const express = require('express');
const morgan = require('morgan');

const JobManager = require('./job-manager');
const HistoryManager = require('./history-manager');
const { CpuAllocator } = require('./cpu-allocator');
const {
  TOOL_DEFINITIONS,
  TOOL_METADATA,
  ENGINE_DEFINITIONS,
  ENGINE_METADATA,
  MATCH_MODES,
  DEFAULT_OPTIONS
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
  const fs = require('fs');
  const historyPath = path.join(__dirname, '..', 'data', 'history.jsonl');
  const configPath = path.join(__dirname, '..', 'config', 'settings.json');

  // Ensure data and config directories exist
  try {
    const dataDir = path.dirname(historyPath);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    const configDir = path.dirname(configPath);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
  } catch (err) {
    console.error('Failed to create directories:', err);
  }

  function getSettings() {
    try {
      if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath, 'utf8'));
      }
    } catch (e) {
      console.error('Error reading config:', e);
    }
    return {};
  }

  function saveSettings(newSettings) {
    try {
      const current = getSettings();
      const next = { ...current, ...newSettings };
      fs.writeFileSync(configPath, JSON.stringify(next, null, 2));
      return next;
    } catch (e) {
      console.error('Error writing config:', e);
      return {};
    }
  }

  const historyManager = new HistoryManager(historyPath);
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
    const s = getSettings();
    res.json({
      tools: TOOL_METADATA,
      engines: ENGINE_METADATA,
      matchModes: MATCH_MODES,
      defaults: {
        toolTimeoutSeconds: s.toolTimeoutSeconds ?? Math.round(DEFAULT_OPTIONS.toolTimeoutMs / 1000),
        engineTimeoutSeconds: s.engineTimeoutSeconds ?? Math.round(DEFAULT_OPTIONS.engineTimeoutMs / 1000),
        maxRepeatTimes: s.maxRepeatTimes ?? DEFAULT_OPTIONS.maxRepeatTimes,
        maxAttackLength: s.maxAttackLength ?? DEFAULT_OPTIONS.maxAttackLength,

        toolCores: s.toolCores ?? (DEFAULT_OPTIONS.defaultCores || null),
        toolMemory: s.toolMemory ?? (DEFAULT_OPTIONS.defaultMemoryMB || null),

        engineCores: s.engineCores ?? (DEFAULT_OPTIONS.defaultCores || null),
        engineMemory: s.engineMemory ?? (DEFAULT_OPTIONS.defaultMemoryMB || null),

        matchMode: s.matchMode ?? 0,
        repeatOverride: s.repeatOverride ?? null
      }
    });
  });

  app.post('/api/settings', (req, res) => {
    const updated = saveSettings(req.body);
    res.json({ status: 'ok', settings: updated });
  });

  app.get('/api/history', async (req, res) => {
    try {
      const history = await historyManager.getRecent(50);
      res.json(history);
    } catch (err) {
      res.status(500).json({ error: 'Failed to fetch history' });
    }
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

    const timeoutSeconds = Number(req.body?.timeoutSeconds);
    const cpuCores = Number(req.body?.cpuCores);
    const memoryMB = Number(req.body?.memoryMB);
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
        timeoutMs: timeoutMs || DEFAULT_OPTIONS.toolTimeoutMs,
        cpuCores: Number.isFinite(cpuCores) && cpuCores > 0 ? cpuCores : (DEFAULT_OPTIONS.defaultCores || null),
        memoryMB: Number.isFinite(memoryMB) && memoryMB > 0 ? memoryMB : (DEFAULT_OPTIONS.defaultMemoryMB || null)
      }
    });

    historyManager.append({
      type: 'tools',
      regex,
      detail: `${toolIds.length} tools`
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

    historyManager.append({
      type: 'engines',
      regex,
      detail: `${engines.length} engines`
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

  // Expose regex-colorizer for frontend import
  app.use('/vendor/regex-colorizer', express.static(path.join(__dirname, '..', 'node_modules', 'regex-colorizer')));
  
  // Expose CodeMirror 6 and dependencies
  const vendorModules = [
    'codemirror',
    '@codemirror',
    '@lezer',
    '@marijn',
    'style-mod',
    'w3c-keyname',
    'crelt'
  ];
  
  vendorModules.forEach(mod => {
    app.use(`/vendor/${mod}`, express.static(path.join(__dirname, '..', 'node_modules', mod)));
  });

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
