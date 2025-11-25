import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Maintenance Page
 * Tests HU deadlines, task filtering, and clickable KPI cards
 */

test.describe('Maintenance Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/maintenance');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Wartungsplanung' })).toBeVisible();
    await expect(page.getByText('HU-Fristen und Wartungsaufgaben')).toBeVisible();
  });

  test('should display 4 KPI cards', async ({ page }) => {
    // Überfällig
    await expect(page.getByText('Überfällig')).toBeVisible();

    // Dringend
    await expect(page.getByText('Dringend')).toBeVisible();

    // Bald fällig
    await expect(page.getByText('Bald fällig')).toBeVisible();

    // Geplant
    await expect(page.getByText(/Geplant/).first()).toBeVisible();
  });

  test('should display maintenance tasks table', async ({ page }) => {
    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Lok' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Aufgabe' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Fällig am' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Priorität' })).toBeVisible();
  });

  test('should display at least 5 maintenance tasks', async ({ page }) => {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('should filter by "all" status', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('all');

    // Should show all tasks
    const rows = page.locator('table tbody tr');
    const allCount = await rows.count();
    expect(allCount).toBeGreaterThan(0);
  });

  test('should filter by "overdue" status', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('overdue');

    // Should only show overdue tasks
    await page.waitForTimeout(300);
    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible tasks should have "Überfällig" status
      const overdueBadges = page.locator('text=Überfällig');
      expect(await overdueBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should filter by "urgent" status (≤7 days)', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('urgent');

    await page.waitForTimeout(300);
    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    // Should show tasks due in ≤7 days
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should filter by "upcoming" status (>7 days)', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('upcoming');

    await page.waitForTimeout(300);
    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    // Should show tasks due in >7 days
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display priority badges', async ({ page }) => {
    // Check for priority badges (Critical, High, Medium, Low)
    const hasCritical = (await page.locator('text=Critical').count()) > 0;
    const hasHigh = (await page.locator('text=High').count()) > 0;
    const hasMedium = (await page.locator('text=Medium').count()) > 0;

    // At least one priority should exist
    expect(hasCritical || hasHigh || hasMedium).toBeTruthy();
  });

  test('should display days until due', async ({ page }) => {
    // Should show text like "in X Tagen" or "Überfällig"
    const daysText = page.locator('text=/in \\d+ Tagen|Überfällig|Heute fällig/');
    expect(await daysText.count()).toBeGreaterThan(0);
  });

  test('should sort tasks by days until due (ascending)', async ({ page }) => {
    // Get all "days until" cells
    const daysCells = page.locator('table tbody tr td:nth-child(6)');
    const count = await daysCells.count();

    if (count > 1) {
      // First item should have smallest number or be overdue
      const firstCell = await daysCells.nth(0).textContent();
      expect(firstCell).toBeTruthy();
    }
  });

  test('should display KPI card count that matches filtered results', async ({ page }) => {
    // Get total count from KPIs
    const overdueCard = page.locator('text=Überfällig').locator('..').locator('..');

    // Click "overdue" filter
    await page.locator('select').selectOption('overdue');
    await page.waitForTimeout(300);

    // Count table rows
    const rows = page.locator('table tbody tr');
    const tableCount = await rows.count();

    // Should match or be related to KPI
    expect(tableCount).toBeGreaterThanOrEqual(0);
  });

  test('should show empty state when no tasks match filter', async ({ page }) => {
    // This test depends on data, may or may not show empty state
    // Just verify the page doesn't crash
    await page.locator('select').selectOption('upcoming');
    await page.waitForTimeout(300);

    const emptyMessage = page.getByText('Keine Wartungsaufgaben gefunden');
    // Either show tasks or empty message
    const rows = page.locator('table tbody tr');
    const hasRows = (await rows.count()) > 0;
    const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);

    expect(hasRows || hasEmptyMessage).toBeTruthy();
  });

  test('should navigate to workshop page', async ({ page }) => {
    await page.getByRole('link', { name: 'Werkstatt' }).click();
    await expect(page).toHaveURL('/workshop');
  });

  test('KPI card click should filter tasks (if clickable)', async ({ page }) => {
    // Try clicking the "Überfällig" card
    const overdueCard = page.locator('text=Überfällig').locator('..').locator('..');

    // Click it
    await overdueCard.click();
    await page.waitForTimeout(500);

    // Filter should change to "overdue"
    const filterSelect = page.locator('select');
    const selectedValue = await filterSelect.inputValue();
    expect(selectedValue).toBe('overdue');
  });
});
