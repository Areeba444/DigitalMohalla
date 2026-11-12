import { test, expect } from '@playwright/test';

test.describe('Digital Mohalla Navigation & NFR-U-01 Web E2E Loop', () => {
  test('landing screen renders without errors and contains no composite trust score', async ({ page }) => {
    await page.goto('/');
    // Check that page loads
    await expect(page).toHaveTitle(/Digital Mohalla|Expo/i);

    // Verify NFR-U-01 compliance across all visible text on initial render
    const bodyText = await page.innerText('body');
    expect(bodyText).not.toMatch(/\b[1-5](\.[0-9])?\s*\/\s*5\b/);
    expect(bodyText).not.toMatch(/★/);
    expect(bodyText).not.toMatch(/trust\s*score\s*:\s*[0-9]+/i);
  });
});

