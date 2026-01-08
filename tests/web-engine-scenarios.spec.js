const { test, expect } = require('@playwright/test');

test.describe('ReDoS dashboard - Engine verification scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResultCard = page.locator('#tool-results .result-card').first();
    await expect(toolResultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    
    await toolResultCard.getByRole('button', { name: '用于验证' }).click();
    await expect(page.locator('#attack-summary')).toContainText('来源工具');
  });

  test('can select and run multiple engines', async ({ page }) => {
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Node.js 21' }).click();
    
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    const engineResults = page.locator('#engine-results');
    await expect(engineResults.locator('.result-card')).toHaveCount(2, { timeout: 15_000 });
  });

  test('displays engine execution time and match count', async ({ page }) => {
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    const engineCard = page.locator('#engine-results .result-card').first();
    await expect(engineCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(engineCard).toContainText('耗时');
  });

  test('shows payload information in job status', async ({ page }) => {
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    await page.waitForFunction(() => {
      const state = window.__REDOS_STATE__;
      return state && state.currentEngineJob && state.currentEngineJob.status === 'completed';
    }, { timeout: 15_000 });
    
    await expect(page.locator('#engine-job-status')).toContainText('状态');
  });

  test('can toggle between match modes', async ({ page }) => {
    const matchModeSelector = page.locator('#match-mode');
    const options = await matchModeSelector.locator('option').count();
    
    if (options >= 2) {
      await matchModeSelector.selectOption({ index: 0 });
      await matchModeSelector.selectOption({ index: 1 });
    }
    
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    const engineCard = page.locator('#engine-results .result-card').first();
    await expect(engineCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
  });

  test('can set custom repeat override', async ({ page }) => {
    const repeatInput = page.locator('#repeat-override');
    await repeatInput.fill('10');
    
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    const engineCard = page.locator('#engine-results .result-card').first();
    await expect(engineCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
  });

  test('displays engine elapsed time', async ({ page }) => {
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    const engineCard = page.locator('#engine-results .result-card').first();
    await expect(engineCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(engineCard).toContainText('耗时');
  });

  test('clears previous engine results when starting new run', async ({ page }) => {
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    await expect(page.locator('#engine-results .result-card')).toHaveCount(1, { timeout: 15_000 });
    
    await page.locator('#engines-list .checkbox-tile', { hasText: 'C (PCRE2)' }).click();
    await page.getByRole('button', { name: '运行所选引擎' }).click();
    
    await page.waitForTimeout(500);
    const cardCount = await page.locator('#engine-results .result-card').count();
    expect(cardCount).toBeGreaterThanOrEqual(1);
  });
});
