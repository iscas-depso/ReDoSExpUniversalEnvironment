const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const http = require('http');
const { createApp } = require('../../server/app');

describe('API Integration', () => {
  let app;
  let server;
  let baseUrl;
  let lastToolRunOpts = null;
  let lastEngineRunOpts = null;

  before(async () => {
    const mockRunTools = async (jm, job, opts) => {
      lastToolRunOpts = opts;
      jm.updateJob(job, { status: 'running' });
      for (const toolId of opts.toolIds) {
        jm.updateResult(job, toolId, r => {
          r.status = 'completed';
          r.output = toolId === 'grewia'
            ? {
                is_redos: true,
                elapsed_ms: 10,
                prefix: '',
                infix: '',
                suffix: '',
                repeat_times: -1,
                recommendedCandidateId: 'candidate-1',
                candidates: [
                  {
                    id: 'candidate-1',
                    label: 'Candidate 1',
                    attack: {
                      fullText: Buffer.from('aaaaab', 'utf8').toString('base64')
                    },
                    preview: 'aaaaab',
                    payloadLength: 6
                  }
                ]
              }
            : { is_redos: true, elapsed_ms: 10, prefix: '', infix: 'YQ==', suffix: '', repeat_times: 4 };
        });
        jm.incrementProgress(job);
      }
      jm.finalizeJob(job, 'completed');
    };

    const mockRunEngines = async (jm, job, opts) => {
      lastEngineRunOpts = opts;
      jm.updateJob(job, { status: 'running' });
      for (const engineId of opts.engines) {
        jm.updateResult(job, engineId, r => {
          r.status = 'completed';
          r.output = { elapsed_ms: 5, match_count: 1 };
        });
        jm.incrementProgress(job);
      }
      jm.finalizeJob(job, 'completed');
    };

    app = createApp({
      runTools: mockRunTools,
      runEngines: mockRunEngines,
      logError: () => {}
    });

    await new Promise((resolve) => {
      server = app.listen(0, '127.0.0.1', () => {
        const addr = server.address();
        baseUrl = `http://127.0.0.1:${addr.port}`;
        resolve();
      });
    });
  });

  after(() => {
    if (server) {
      server.close();
    }
    if (app && app.locals && app.locals.jobManager) {
      app.locals.jobManager.stopCleanup();
    }
  });

  function request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const url = new URL(path, baseUrl);
      const options = {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {}
      };

      const req = http.request(options, res => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, body: data ? JSON.parse(data) : null, headers: res.headers });
          } catch {
            resolve({ status: res.statusCode, body: data, headers: res.headers });
          }
        });
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy(new Error('Request timeout'));
      });

      if (body) {
        req.write(JSON.stringify(body));
      }
      req.end();
    });
  }

  describe('GET /api/meta', () => {
    it('returns tool and engine metadata', async () => {
      const res = await request('GET', '/api/meta');
      
      assert.strictEqual(res.status, 200);
      assert.ok(Array.isArray(res.body.tools));
      assert.ok(Array.isArray(res.body.engines));
      assert.ok(Array.isArray(res.body.matchModes));
      assert.ok(res.body.defaults);
    });

    it('includes all 7 tools', async () => {
      const res = await request('GET', '/api/meta');
      
      const toolIds = res.body.tools.map(t => t.id);
      assert.ok(toolIds.includes('regexploit'));
      assert.ok(toolIds.includes('regexstatic'));
      assert.ok(toolIds.includes('rescue'));
      assert.ok(toolIds.includes('rengar'));
      assert.ok(toolIds.includes('redoshunter'));
      assert.ok(toolIds.includes('regulator'));
      assert.ok(toolIds.includes('grewia'));
    });

    it('includes GREWIA option schema', async () => {
      const res = await request('GET', '/api/meta');

      const grewia = res.body.tools.find(tool => tool.id === 'grewia');
      assert.ok(grewia);
      assert.ok(Array.isArray(grewia.optionsSchema));
      assert.ok(grewia.optionsSchema.some(option => option.key === 'regexEngine'));
      assert.strictEqual(grewia.defaultOptions.candidateMode, 'single');
    });

    it('includes all 19 engines', async () => {
      const res = await request('GET', '/api/meta');
      
      assert.strictEqual(res.body.engines.length, 19);
    });
  });

  describe('POST /api/jobs/tools', () => {
    it('rejects missing regex', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        tools: ['regexploit']
      });
      
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error.includes('Regex'));
    });

    it('rejects empty tools array', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: []
      });
      
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error.includes('tool'));
    });

    it('rejects invalid tool ids', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: ['invalid-tool']
      });
      
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error.includes('Unsupported'));
    });

    it('accepts valid request and returns job id', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: ['regexploit']
      });
      
      assert.strictEqual(res.status, 202);
      assert.ok(res.body.jobId);
      assert.strictEqual(res.body.status, 'queued');
    });

    it('accepts normalized GREWIA tool options', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: ['grewia'],
        toolOptions: {
          grewia: {
            regexEngine: 'Python',
            matchMode: 1,
            attackStringLength: 4096,
            candidateMode: 'multiple',
            decremental: true
          }
        }
      });

      assert.strictEqual(res.status, 202);
      await new Promise(r => setTimeout(r, 50));
      assert.deepStrictEqual(lastToolRunOpts.toolOptions.grewia, {
        regexEngine: 'Python',
        matchMode: 1,
        attackStringLength: 4096,
        candidateMode: 'multiple',
        decremental: true
      });
    });

    it('rejects invalid GREWIA tool options', async () => {
      const res = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: ['grewia'],
        toolOptions: {
          grewia: {
            regexEngine: 'PCRE2'
          }
        }
      });

      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error.includes('regexEngine'));
    });
  });

  describe('POST /api/jobs/engines', () => {
    it('rejects missing regex', async () => {
      const res = await request('POST', '/api/jobs/engines', {
        engines: ['python'],
        attack: { prefix: '', infix: 'YQ==', suffix: '' }
      });
      
      assert.strictEqual(res.status, 400);
    });

    it('rejects missing attack data', async () => {
      const res = await request('POST', '/api/jobs/engines', {
        regex: '(a+)+',
        engines: ['python']
      });
      
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error.toLowerCase().includes('attack'));
    });

    it('rejects invalid engine ids', async () => {
      const res = await request('POST', '/api/jobs/engines', {
        regex: '(a+)+',
        engines: ['invalid-engine'],
        attack: { prefix: '', infix: 'YQ==', suffix: '' }
      });
      
      assert.strictEqual(res.status, 400);
    });

    it('accepts valid request', async () => {
      const res = await request('POST', '/api/jobs/engines', {
        regex: '(a+)+',
        engines: ['python'],
        attack: { prefix: '', infix: 'YQ==', suffix: '', repeat_times: 10 }
      });
      
      assert.strictEqual(res.status, 202);
      assert.ok(res.body.jobId);
    });

    it('accepts fullText attack payloads for GREWIA candidates', async () => {
      const fullText = Buffer.from('aaaaab', 'utf8').toString('base64');
      const res = await request('POST', '/api/jobs/engines', {
        regex: '(a+)+',
        engines: ['python'],
        attack: { fullText },
        attackSource: {
          toolId: 'grewia',
          candidateId: 'candidate-1',
          candidateLabel: 'Candidate 1'
        },
        repeatOverride: 123
      });

      assert.strictEqual(res.status, 202);
      await new Promise(r => setTimeout(r, 50));
      assert.deepStrictEqual(lastEngineRunOpts.attack, { fullText });
      assert.deepStrictEqual(lastEngineRunOpts.attackSource, {
        toolId: 'grewia',
        candidateId: 'candidate-1',
        candidateLabel: 'Candidate 1'
      });
      assert.strictEqual(lastEngineRunOpts.repeatOverride, 123);
    });
  });

  describe('GET /api/jobs/:id', () => {
    it('returns 404 for non-existent job', async () => {
      const res = await request('GET', '/api/jobs/non-existent-id');
      
      assert.strictEqual(res.status, 404);
    });

    it('returns job status after creation', async () => {
      const createRes = await request('POST', '/api/jobs/tools', {
        regex: '(a+)+',
        tools: ['regexploit']
      });
      
      await new Promise(r => setTimeout(r, 50));
      
      const jobRes = await request('GET', `/api/jobs/${createRes.body.jobId}`);
      
      assert.strictEqual(jobRes.status, 200);
      assert.ok(['queued', 'running', 'completed'].includes(jobRes.body.status));
    });
  });

  describe('404 handling', () => {
    it('returns 404 for unknown API routes', async () => {
      const res = await request('GET', '/api/unknown');
      
      assert.strictEqual(res.status, 404);
    });
  });
});
