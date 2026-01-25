#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://192.168.1.34:8080';
const SCREENSHOT_DIR = path.join(__dirname, '..', 'test-results', 'linux-screenshots');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  try {
    console.log(`\n=== Test 1: Initial Dashboard (${BASE_URL}) ===`);
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-initial-dashboard.png') });
    console.log('Screenshot: 01-initial-dashboard.png');

    const title = await page.title();
    console.log(`Page title: ${title}`);

    const toolCount = await page.locator('#tools-list input[type="checkbox"]').count();
    const engineCount = await page.locator('#engines-list input[type="checkbox"]').count();
    console.log(`Found ${toolCount} tools, ${engineCount} engines`);

    console.log('\n=== Test 2: Enter Regex and Select Tool ===');
    await page.fill('#regex-input', '(a+)+b');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-regex-entered.png') });

    await page.click('label:has-text("RegExploit")');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-tool-selected.png') });
    console.log('Screenshot: 03-tool-selected.png');

    console.log('\n=== Test 3: Run Tool Detection ===');
    await page.click('#run-tools');
    console.log('Clicked run button, waiting for results...');

    await page.waitForSelector('.result-card', { timeout: 60000 });
    await sleep(3000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04-tool-running.png') });

    try {
      await page.waitForSelector('.result-card .badge-status.status-completed, .result-card .badge-status.status-failed', { timeout: 60000 });
    } catch (e) {
      console.log('Timeout waiting for completion, capturing current state');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05-tool-results.png'), fullPage: true });
    console.log('Screenshot: 05-tool-results.png');

    const resultCard = page.locator('.result-card').first();
    const statusBadge = await resultCard.locator('.badge-status').textContent().catch(() => 'unknown');
    console.log(`Tool result status: ${statusBadge}`);

    const isRedos = await page.locator('.badge-redos-true, .badge-redos-false, .result-card:has-text("is_redos") >> text=/true|false/i').first().textContent().catch(() => 'N/A');
    console.log(`Is ReDoS: ${isRedos}`);

    console.log('\n=== Test 4: Select Attack for Verification ===');
    const useBtn = page.locator('button:has-text("用于验证"), button:has-text("Use for Verification")').first();
    if (await useBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await useBtn.click();
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06-attack-selected.png') });
      console.log('Screenshot: 06-attack-selected.png');

      console.log('\n=== Test 5: Run Engine Verification ===');
      await page.click('#engines-list label:has-text("Python")');
      await sleep(500);

      const repeatInput = page.locator('#repeat-override');
      if (await repeatInput.isVisible()) {
        await repeatInput.fill('10');
        console.log('Set repeat override to 10 to speed up test');
      }

      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07-engine-selected.png') });

      await page.waitForSelector('#run-engines:not([disabled])', { timeout: 10000 });
      await page.click('#run-engines');
      console.log('Running engine verification...');

      await sleep(3000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08-engine-running.png') });

      try {
        // Wait up to 2 minutes for real engine execution
        await page.waitForSelector('#engine-results .result-card .badge-status.status-completed, #engine-results .result-card .badge-status.status-failed', { timeout: 120000 });
      } catch (e) {
        console.log('Engine timeout, capturing state');
      }

      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09-engine-results.png'), fullPage: true });
      console.log('Screenshot: 09-engine-results.png');

      const engineStatus = await page.locator('#engine-results .result-card .badge-status').first().textContent().catch(() => 'unknown');
      console.log(`Engine result status: ${engineStatus}`);
    } else {
      console.log('No attack available for verification');
    }

    console.log('\n=== Test 6: Multiple Tools ===');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.fill('#regex-input', '(x+x+)+y');
    await page.click('#tools-list label:has-text("RegExploit")');
    await page.click('#tools-list label:has-text("ReScue")');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10-multi-tool-selected.png') });

    await page.click('#run-tools');
    await sleep(5000);

    try {
      await page.waitForSelector('.result-card .badge-status.status-completed', { timeout: 90000 });
    } catch (e) {
      console.log('Multi-tool timeout');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11-multi-tool-results.png'), fullPage: true });
    console.log('Screenshot: 11-multi-tool-results.png');

    console.log(`\n=== Screenshots saved to: ${SCREENSHOT_DIR} ===`);

  } catch (error) {
    console.error('Test error:', error.message);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'error-state.png'), fullPage: true });
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
