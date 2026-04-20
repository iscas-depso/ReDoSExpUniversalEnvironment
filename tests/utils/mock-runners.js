const { Buffer } = require('buffer');

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function encode(value) {
  return Buffer.from(value, 'utf8').toString('base64');
}

async function mockRunToolsJob(jobManager, job, { regex, toolIds }) {
  if (process.env.PLAYWRIGHT_DEBUG) {
    // eslint-disable-next-line no-console
    console.log('[mockRunToolsJob] starting for tools:', toolIds);
  }
  jobManager.updateJob(job, { status: 'running' });

  for (const toolId of toolIds) {
    jobManager.updateResult(job, toolId, result => {
      result.status = 'running';
      result.startedAt = new Date().toISOString();
    });

    await sleep(25);

    jobManager.updateResult(job, toolId, result => {
      result.status = 'completed';
      result.finishedAt = new Date().toISOString();
      result.elapsedMs = result.elapsedMs ?? 12;
      result.output = toolId === 'grewia'
        ? {
            elapsed_ms: 12,
            is_redos: true,
            prefix: '',
            infix: '',
            suffix: '',
            repeat_times: -1,
            recommendedCandidateId: 'candidate-1',
            candidates: [
              {
                id: 'candidate-1',
                label: 'Candidate 1',
                attack: { fullText: encode('aaaaab') },
                preview: 'aaaaab',
                payloadLength: 6,
                metadata: { index: 1, mode: 'fullText' }
              },
              {
                id: 'candidate-2',
                label: 'Candidate 2',
                attack: { fullText: encode('aaaaaab') },
                preview: 'aaaaaab',
                payloadLength: 7,
                metadata: { index: 2, mode: 'fullText' }
              }
            ],
            toolMeta: {
              normalizedOptions: {
                regexEngine: 'Java',
                matchMode: 0,
                attackStringLength: 100000,
                candidateMode: 'multiple',
                decremental: false
              },
              candidateCount: 2
            }
          }
        : {
            elapsed_ms: 12,
            is_redos: true,
            prefix: encode(''),
            infix: encode('a'),
            suffix: encode(''),
            repeat_times: 4
          };
      result.logs = [
        { stream: 'stdout', content: `mock tool ${toolId} processed regex of length ${regex.length}` }
      ];
    });

    jobManager.incrementProgress(job);
  }

  jobManager.finalizeJob(job, 'completed');
}

async function mockRunEnginesJob(jobManager, job, { regex, engines, matchMode }) {
  if (process.env.PLAYWRIGHT_DEBUG) {
    // eslint-disable-next-line no-console
    console.log('[mockRunEnginesJob] starting for engines:', engines);
  }
  const preview = 'a'.repeat(8) + 'b';
  job.metadata = {
    ...(job.metadata || {}),
    payloadInfo: {
      prefixLength: 0,
      infixLength: 1,
      suffixLength: 0,
      appliedRepeat: 4,
      truncated: false,
      payloadLength: preview.length
    },
    payloadPreview: preview
  };

  jobManager.updateJob(job, {
    status: 'running',
    metadata: job.metadata
  });

  for (const engineId of engines) {
    jobManager.updateResult(job, engineId, result => {
      result.status = 'running';
      result.startedAt = new Date().toISOString();
    });

    await sleep(25);

    jobManager.updateResult(job, engineId, result => {
      result.status = 'completed';
      result.finishedAt = new Date().toISOString();
      result.elapsedMs = result.elapsedMs ?? 5;
      result.output = {
        elapsed_ms: 5.123,
        match_count: matchMode === 1 ? 1 : 4,
        raw: '5.123 - 4'
      };
      result.logs = [
        { stream: 'stdout', content: `mock engine ${engineId} benchmarked regex length ${regex.length}` }
      ];
    });

    jobManager.incrementProgress(job);
  }

  jobManager.finalizeJob(job, 'completed');
}

module.exports = {
  mockRunToolsJob,
  mockRunEnginesJob
};
