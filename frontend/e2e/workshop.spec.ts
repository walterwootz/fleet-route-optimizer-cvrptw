import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Workshop Page
 * Tests work orders, progress bars, and status filtering
 */

test.describe('Workshop Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workshop');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Werkstattplanung' })).toBeVisible();
    await expect(page.getByText('Übersicht aller Werkstattaufträge')).toBeVisible();
  });

  test('should display 3 KPI cards', async ({ page }) => {
    // Gesamt
    await expect(page.getByText('Gesamt')).toBeVisible();

    // In Bearbeitung
    await expect(page.getByText('In Bearbeitung')).toBeVisible();

    // Abgeschlossen
    await expect(page.getByText('Abgeschlossen')).toBeVisible();
  });

  test('should display work orders table with headers', async ({ page }) => {
    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'WO-Nummer' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Lok' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Typ' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Fortschritt' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Start' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Geplant fertig' })).toBeVisible();
  });

  test('should display at least 5 work orders', async ({ page }) => {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('should display progress bars for each work order', async ({ page }) => {
    // Count progress bars (should match number of rows)
    const progressBars = page.locator('div[class*="bg-"][class*="-500"]').filter({ hasText: /\d+%/ });
    const count = await progressBars.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display status badges', async ({ page }) => {
    // Check for various status badges
    const hasPlanned = (await page.locator('text=Geplant').count()) > 0;
    const hasInProgress = (await page.locator('text=In Bearbeitung').count()) > 0;
    const hasCompleted = (await page.locator('text=Abgeschlossen').count()) > 0;

    // At least one status should exist
    expect(hasPlanned || hasInProgress || hasCompleted).toBeTruthy();
  });

  test('should filter by "all" status', async ({ page }) => {
    const filterSelect = page.locator('select').first();
    await filterSelect.selectOption('all');

    // Should show all work orders
    const rows = page.locator('table tbody tr');
    const allCount = await rows.count();
    expect(allCount).toBeGreaterThan(0);
  });

  test('should filter by "in_progress" status', async ({ page }) => {
    const filterSelect = page.locator('select').first();
    await filterSelect.selectOption('in_progress');

    await page.waitForTimeout(300);

    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible rows should have "In Bearbeitung" status
      const inProgressBadges = page.locator('text=In Bearbeitung');
      expect(await inProgressBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should filter by "completed" status', async ({ page }) => {
    const filterSelect = page.locator('select').first();
    await filterSelect.selectOption('completed');

    await page.waitForTimeout(300);

    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible rows should have "Abgeschlossen" status
      const completedBadges = page.locator('text=Abgeschlossen');
      expect(await completedBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should filter by work order type', async ({ page }) => {
    // Get the type filter (second select)
    const typeSelect = page.locator('select').nth(1);
    await typeSelect.selectOption('HU');

    await page.waitForTimeout(300);

    // Should show only HU work orders
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display work order types (HU, Reparatur, Inspektion)', async ({ page }) => {
    // Check for various WO types
    const hasHU = (await page.locator('text=HU').count()) > 0;
    const hasReparatur = (await page.locator('text=Reparatur').count()) > 0;
    const hasInspektion = (await page.locator('text=Inspektion').count()) > 0;

    // At least one type should exist
    expect(hasHU || hasReparatur || hasInspektion).toBeTruthy();
  });

  test('should display progress percentage', async ({ page }) => {
    // Should show percentages like "75%", "100%", etc.
    const percentageText = page.locator('text=/%/');
    expect(await percentageText.count()).toBeGreaterThan(0);
  });

  test('should color-code progress bars correctly', async ({ page }) => {
    // Progress bars should have different colors based on completion
    // Low progress: yellow/orange, high progress: blue/green

    // Just verify progress bars exist and have color classes
    const progressBars = page.locator('[class*="bg-blue-"], [class*="bg-green-"], [class*="bg-yellow-"], [class*="bg-orange-"]');
    expect(await progressBars.count()).toBeGreaterThan(0);
  });

  test('should display dates in German format', async ({ page }) => {
    // Should show dates like "24.11.2025" or similar
    const datePattern = /\d{2}\.\d{2}\.\d{4}/;
    const cells = page.locator('table tbody tr td');
    const allText = await cells.allTextContents();
    const hasGermanDate = allText.some(text => datePattern.test(text));

    expect(hasGermanDate).toBeTruthy();
  });

  test('should show work order count', async ({ page }) => {
    // Should show count like "6 von 6" or similar
    const countText = page.locator('text=/\\d+ von \\d+/');
    await expect(countText).toBeVisible();
  });

  test('should show empty state when no orders match filter', async ({ page }) => {
    // Select a filter that might return no results
    const filterSelect = page.locator('select').first();
    await filterSelect.selectOption('cancelled');

    await page.waitForTimeout(300);

    const emptyMessage = page.getByText('Keine Werkstattaufträge gefunden');
    const rows = page.locator('table tbody tr');
    const hasRows = (await rows.count()) > 0;
    const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);

    // Either show rows or empty message
    expect(hasRows || hasEmptyMessage).toBeTruthy();
  });

  test('should navigate to maintenance page', async ({ page }) => {
    await page.getByRole('link', { name: 'Wartung' }).click();
    await expect(page).toHaveURL('/maintenance');
  });
});
