const http = require('http');

const { createApp } = require('../../server/app');
const { mockRunToolsJob, mockRunEnginesJob } = require('./mock-runners');

const PORT = Number(process.env.PORT) || 3100;

const app = createApp({
  runTools: mockRunToolsJob,
  runEngines: mockRunEnginesJob,
  logError: (...args) => {
    if (process.env.PLAYWRIGHT_DEBUG) {
      console.error('[mock-runner]', ...args);
    }
  }
});

const server = http.createServer(app);

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Mock ReDoS server listening on http://127.0.0.1:${PORT}`);
});

function shutdown() {
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
