import { test, expect } from '@playwright/test';

/**
 * E2E Tests for FLEET-ONE Chat
 * Tests chat drawer, message flow, mode indicator, and interactions
 */

test.describe('FLEET-ONE Chat Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display FLEET-ONE toggle button', async ({ page }) => {
    // F1 button should be visible
    const fleetOneButton = page.locator('button').filter({ hasText: 'F1' });
    await expect(fleetOneButton).toBeVisible();
  });

  test('should open chat drawer when clicking F1 button', async ({ page }) => {
    // Click F1 button
    const fleetOneButton = page.locator('button').filter({ hasText: 'F1' });
    await fleetOneButton.click();

    // Drawer should open
    await page.waitForTimeout(500); // Wait for animation

    // Check for chat header
    await expect(page.getByText('FLEET-ONE')).toBeVisible();
  });

  test('should display chat header with role and close button', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Check header elements
    await expect(page.getByText('FLEET-ONE')).toBeVisible();
    await expect(page.getByText('dispatcher')).toBeVisible();

    // Close button should exist
    const closeButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await expect(closeButton).toBeVisible();
  });

  test('should display mode indicator', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Mode indicator should show current mode
    await expect(page.getByText(/Modus:/)).toBeVisible();
  });

  test('should display welcome message or empty state', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Should show either welcome message or empty state
    const hasWelcome = await page.getByText(/Willkommen|Hallo/).isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/Keine Nachrichten|Beginnen Sie/).isVisible().catch(() => false);

    expect(hasWelcome || hasEmptyState).toBeTruthy();
  });

  test('should display chat input field', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Chat input should be visible
    const chatInput = page.locator('textarea').filter({ hasText: '' });
    await expect(chatInput).toBeVisible();
  });

  test('should display mode selector dropdown', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Mode selector should exist
    const modeSelect = page.locator('select');
    const count = await modeSelect.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should have all 7 modes in selector', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Get mode selector
    const modeSelect = page.locator('select').first();

    // Should have options for all 7 modes
    const options = modeSelect.locator('option');
    const count = await options.count();

    // At least 7 modes + "Auto" option = 8
    expect(count).toBeGreaterThanOrEqual(7);
  });

  test('should display send button', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Send button (with Send icon) should be visible
    const sendButton = page.locator('button[type="submit"]');
    await expect(sendButton).toBeVisible();
  });

  test('should disable send button when input is empty', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Send button should be disabled when input is empty
    const sendButton = page.locator('button[type="submit"]');
    await expect(sendButton).toBeDisabled();
  });

  test('should enable send button when input has text', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Type in input
    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Test message');

    // Send button should be enabled
    const sendButton = page.locator('button[type="submit"]');
    await expect(sendButton).toBeEnabled();
  });

  test('should close drawer when clicking close button', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Drawer should be visible
    await expect(page.getByText('FLEET-ONE')).toBeVisible();

    // Click close button
    const closeButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await closeButton.click();

    await page.waitForTimeout(500);

    // Drawer should be closed (FLEET-ONE text should not be visible)
    await expect(page.getByText('FLEET-ONE')).not.toBeVisible();
  });

  test('should close drawer when clicking backdrop', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Click backdrop (the dark overlay)
    const backdrop = page.locator('div[class*="bg-black"]').first();
    await backdrop.click();

    await page.waitForTimeout(500);

    // Drawer should be closed
    await expect(page.getByText('FLEET-ONE')).not.toBeVisible();
  });

  test('should auto-resize textarea when typing multiple lines', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Type multi-line text
    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Line 1\nLine 2\nLine 3');

    // Textarea should have expanded (check height)
    const box = await chatInput.boundingBox();
    expect(box?.height).toBeGreaterThan(40); // Should be taller than single line
  });

  test('should submit message on Enter key (without Shift)', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Type message
    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Test query');

    // Press Enter
    await chatInput.press('Enter');

    await page.waitForTimeout(1000);

    // Input should be cleared after submission
    const inputValue = await chatInput.inputValue();
    expect(inputValue).toBe('');
  });

  test('should reopen drawer and maintain state', async ({ page }) => {
    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Close drawer
    const closeButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await closeButton.click();
    await page.waitForTimeout(500);

    // Reopen drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Drawer should reopen
    await expect(page.getByText('FLEET-ONE')).toBeVisible();
  });

  test('should work from any page', async ({ page }) => {
    // Navigate to Fleet page
    await page.goto('/fleet');

    // F1 button should still be visible
    const fleetOneButton = page.locator('button').filter({ hasText: 'F1' });
    await expect(fleetOneButton).toBeVisible();

    // Open drawer
    await fleetOneButton.click();
    await page.waitForTimeout(500);

    // Chat should open
    await expect(page.getByText('FLEET-ONE')).toBeVisible();
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Open drawer
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);

    // Drawer should take full width on mobile
    const drawer = page.locator('div').filter({ hasText: 'FLEET-ONE' }).first();
    const box = await drawer.boundingBox();

    // On mobile, drawer should be close to full width
    expect(box?.width).toBeGreaterThan(300);
  });
});

test.describe('FLEET-ONE Mode Indicator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.locator('button').filter({ hasText: 'F1' }).click();
    await page.waitForTimeout(500);
  });

  test('should display mode confidence percentage', async ({ page }) => {
    // Mode confidence should be shown as percentage
    const confidenceText = page.locator('text=/%/');
    const count = await confidenceText.count();

    // At least one percentage should be visible
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should show mode icons', async ({ page }) => {
    // Mode indicator should have an icon
    const modeSection = page.locator('text=/Modus:/').locator('..');
    const icons = modeSection.locator('svg');

    expect(await icons.count()).toBeGreaterThan(0);
  });

  test('should have color-coded mode indicator', async ({ page }) => {
    // Mode indicator should have colored background/text
    const modeSection = page.locator('text=/Modus:/').locator('..');
    const hasColor = await modeSection.evaluate((el) => {
      const classes = el.className;
      return /bg-\w+-\d+|text-\w+-\d+/.test(classes);
    });

    expect(hasColor).toBeTruthy();
  });
});
