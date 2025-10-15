const { test, expect } = require('@playwright/test');

test.describe('ReDoS dashboard (mocked)', () => {
  test('runs tool detection and engine verification flows', async ({ page }) => {
    page.on('console', msg => {
      // eslint-disable-next-line no-console
      console.log('[page]', msg.type(), msg.text());
    });
    page.on('pageerror', error => {
      // eslint-disable-next-line no-console
      console.error('[page-error]', error);
    });

    await page.goto('/');

    await page.fill('#regex-input', '(a+)+');

    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegexStatic' }).click();

    await page.getByRole('button', { name: '运行所选工具' }).click();

    const toolResults = page.locator('#tool-results');
    await expect(toolResults).toContainText('RegExploit', { timeout: 15_000 });

    const toolResultCard = toolResults.locator('.result-card').first();
    await expect(toolResultCard.locator('.badge-status.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(toolResultCard).toContainText('推荐重复次数');

    await toolResultCard.getByRole('button', { name: '用于验证' }).click();

    await expect(page.locator('#attack-summary')).toContainText('来源工具');

    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    await page.locator('#engines-list .checkbox-tile', { hasText: 'C (PCRE2)' }).click();

    await page.getByRole('button', { name: '运行所选引擎' }).click();

    await page.waitForFunction(() => {
      const state = window.__REDOS_STATE__;
      return state && state.currentEngineJob && state.currentEngineJob.status === 'completed';
    }, { timeout: 15_000 });

    const engineJobData = await page.evaluate(() => window.__REDOS_STATE__.currentEngineJob);
    if (process.env.PLAYWRIGHT_DEBUG) {
      // eslint-disable-next-line no-console
      console.log('[test] engineJobData', engineJobData);
    }

    const engineCard = page.locator('#engine-results .result-card').first();
    await expect(engineCard.locator('.badge-status.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(engineCard.locator('text=查看引擎输出')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#engine-job-status')).toContainText('负载长度', { timeout: 15_000 });

    expect(engineJobData.results).toBeTruthy();
    expect(Array.isArray(engineJobData.results)).toBe(true);
    engineJobData.results.forEach(result => {
      expect(result.output).toBeTruthy();
      expect(typeof result.output.match_count).toBe('number');
    });
  });
});
