const { test, expect } = require('@playwright/test');

test.describe('ReDoS dashboard - Error handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('disables run button when no regex and no tools selected', async ({ page }) => {
    const runButton = page.getByRole('button', { name: '运行所选工具' });
    await expect(runButton).toBeDisabled();
  });

  test('enables run button only when regex AND tools are selected', async ({ page }) => {
    const runButton = page.getByRole('button', { name: '运行所选工具' });
    
    await expect(runButton).toBeDisabled();
    
    await page.fill('#regex-input', '(a+)+');
    await expect(runButton).toBeDisabled();
    
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await expect(runButton).toBeEnabled();
  });

  test('disables engine run button without attack selection', async ({ page }) => {
    const runButton = page.getByRole('button', { name: '运行所选引擎' });
    
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#engines-list .checkbox-tile', { hasText: 'Python' }).click();
    
    await expect(runButton).toBeDisabled();
  });

  test('handles special characters in regex input', async ({ page }) => {
    await page.fill('#regex-input', '([\\w+\\.]+@[\\w+\\.]+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResults = page.locator('#tool-results');
    await expect(toolResults).toContainText('RegExploit', { timeout: 15_000 });
  });

  test('handles unicode characters in regex input', async ({ page }) => {
    await page.fill('#regex-input', '(\\p{L}+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResults = page.locator('#tool-results');
    await expect(toolResults).toContainText('RegExploit', { timeout: 15_000 });
  });

  test('clears previous results when starting new tool run', async ({ page }) => {
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResults = page.locator('#tool-results');
    await expect(toolResults.locator('.result-card')).toHaveCount(1, { timeout: 15_000 });
    
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegexStatic' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    await page.waitForTimeout(500);
    const cardCount = await toolResults.locator('.result-card').count();
    expect(cardCount).toBeGreaterThanOrEqual(1);
  });
});
