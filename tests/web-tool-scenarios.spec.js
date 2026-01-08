const { test, expect } = require('@playwright/test');

test.describe('ReDoS dashboard - Tool scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('can select and run multiple tools simultaneously', async ({ page }) => {
    await page.fill('#regex-input', '(a+)+b');
    
    const toolTiles = page.locator('#tools-list .checkbox-tile');
    const toolCount = await toolTiles.count();
    
    for (let i = 0; i < Math.min(toolCount, 3); i++) {
      await toolTiles.nth(i).click();
    }
    
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResults = page.locator('#tool-results');
    await expect(toolResults.locator('.result-card')).toHaveCount(Math.min(toolCount, 3), { timeout: 30_000 });
  });

  test('displays tool status progression to completed', async ({ page }) => {
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const resultCard = page.locator('#tool-results .result-card').first();
    await expect(resultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
  });

  test('shows tool output with attack data when available', async ({ page }) => {
    await page.fill('#regex-input', '(a+)+');
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    const toolResults = page.locator('#tool-results');
    const resultCard = toolResults.locator('.result-card').first();
    
    await expect(resultCard.locator('.status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(resultCard).toContainText('repeat_times');
  });

  test('can toggle tool selection', async ({ page }) => {
    const regexploitTile = page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' });
    
    await regexploitTile.click();
    await expect(regexploitTile).toHaveClass(/selected|active|checked/);
    
    await regexploitTile.click();
    await expect(regexploitTile).not.toHaveClass(/selected|active|checked/);
  });

  test('preserves regex input after tool run', async ({ page }) => {
    const testRegex = '(a+)+b';
    await page.fill('#regex-input', testRegex);
    await page.locator('#tools-list .checkbox-tile', { hasText: 'RegExploit' }).click();
    await page.getByRole('button', { name: '运行所选工具' }).click();
    
    await expect(page.locator('#tool-results .result-card .status-completed')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#regex-input')).toHaveValue(testRegex);
  });
});
