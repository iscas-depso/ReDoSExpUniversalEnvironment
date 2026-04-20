const { test, expect } = require('@playwright/test');

test.describe('ReDoS dashboard - GREWIA workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'GREWIA' }).click();
  });

  test('shows GREWIA tool options with expected defaults', async ({ page }) => {
    await expect(page.locator('#tool-options-panel')).toBeVisible();
    await expect(page.locator('#tool-option-grewia-regexEngine')).toHaveValue('Java');
    await expect(page.locator('#tool-option-grewia-matchMode')).toHaveValue('0');
    await expect(page.locator('#tool-option-grewia-attackStringLength')).toHaveValue('100000');
    await expect(page.locator('#tool-option-grewia-candidateMode')).toHaveValue('single');
    await expect(page.locator('#tool-option-grewia-decremental')).not.toBeChecked();
  });

  test('sends GREWIA toolOptions in POST /api/jobs/tools', async ({ page }) => {
    await page.locator('#tool-option-grewia-regexEngine').selectOption('Python');
    await page.locator('#tool-option-grewia-matchMode').selectOption('1');
    await page.locator('#tool-option-grewia-attackStringLength').fill('4096');
    await page.locator('#tool-option-grewia-candidateMode').selectOption('multiple');
    await page.locator('#tool-option-grewia-decremental').check();

    const requestPromise = page.waitForRequest(req =>
      req.url().endsWith('/api/jobs/tools') && req.method() === 'POST'
    );

    await page.getByRole('button', { name: '运行所选工具' }).click();

    const request = await requestPromise;
    const payload = request.postDataJSON();

    expect(payload.toolOptions.grewia).toEqual({
      regexEngine: 'Python',
      matchMode: 1,
      attackStringLength: 4096,
      candidateMode: 'multiple',
      decremental: true
    });
  });

  test('renders GREWIA candidates and hides the empty legacy pattern block', async ({ page }) => {
    await page.getByRole('button', { name: '运行所选工具' }).click();

    const resultCard = page.locator('#tool-results .result-card', { hasText: 'GREWIA' }).first();
    await expect(resultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(resultCard).toContainText('Candidate 1 (推荐)');
    await expect(resultCard).toContainText('Candidate 2');
    await expect(resultCard).not.toContainText('Prefix');
    await expect(resultCard).not.toContainText('Suffix');
  });

  test('selecting a GREWIA candidate updates the attack summary and disables repeat override', async ({ page }) => {
    await page.getByRole('button', { name: '运行所选工具' }).click();

    const resultCard = page.locator('#tool-results .result-card', { hasText: 'GREWIA' }).first();
    await expect(resultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await resultCard.locator('.decoded-item').nth(1).getByRole('button', { name: '用于验证' }).click();

    await expect(page.locator('#attack-summary')).toContainText('来源工具: GREWIA');
    await expect(page.locator('#attack-summary')).toContainText('候选: Candidate 2');
    await expect(page.locator('#attack-summary')).toContainText('长度: 7');
    await expect(page.locator('#attack-summary')).toContainText('aaaaaab');
    await expect(page.locator('#repeat-override')).toBeDisabled();
  });

  test('submits attack.fullText and attackSource when verifying a GREWIA candidate', async ({ page }) => {
    await page.getByRole('button', { name: '运行所选工具' }).click();

    const resultCard = page.locator('#tool-results .result-card', { hasText: 'GREWIA' }).first();
    await expect(resultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await resultCard.locator('.decoded-item').nth(0).getByRole('button', { name: '用于验证' }).click();

    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();

    const requestPromise = page.waitForRequest(req =>
      req.url().endsWith('/api/jobs/engines') && req.method() === 'POST'
    );

    await page.getByRole('button', { name: '运行所选引擎' }).click();

    const request = await requestPromise;
    const payload = request.postDataJSON();

    expect(payload.attack).toEqual({
      fullText: Buffer.from('aaaaab', 'utf8').toString('base64')
    });
    expect(payload.attackSource).toEqual(expect.objectContaining({
      toolId: 'grewia',
      candidateId: 'candidate-1',
      candidateLabel: 'Candidate 1'
    }));
    expect(payload.repeatOverride).toBeUndefined();
  });
});
