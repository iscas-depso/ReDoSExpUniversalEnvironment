// @ts-check
const { defineConfig } = require('@playwright/test');

const PORT = Number(process.env.PLAYWRIGHT_PORT) || 3100;

module.exports = defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: {
    timeout: 5_000
  },
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    headless: true
  },
  webServer: {
    command: 'node tests/utils/serve.js',
    url: `http://127.0.0.1:${PORT}`,
    timeout: 30_000,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe'
  }
});
