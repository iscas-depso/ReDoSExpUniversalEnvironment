#!/usr/bin/env node

const { getBatchMeta, runToolBatch, runEngineBatch } = require('../server/batch-cli');

async function readJsonFromStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const text = Buffer.concat(chunks).toString('utf8').trim();
  if (!text) {
    return {};
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Invalid JSON input: ${error.message}`);
  }
}

function writeJson(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

async function main() {
  const command = process.argv[2];

  if (!command || ['meta', 'run-tool', 'run-engine'].indexOf(command) === -1) {
    console.error('Usage: node scripts/batch-backend.js <meta|run-tool|run-engine>');
    process.exit(1);
  }

  try {
    if (command === 'meta') {
      writeJson(getBatchMeta());
      return;
    }

    const payload = await readJsonFromStdin();
    if (command === 'run-tool') {
      writeJson(await runToolBatch(payload));
      return;
    }

    writeJson(await runEngineBatch(payload));
  } catch (error) {
    console.error(error.message || String(error));
    process.exit(1);
  }
}

main();
