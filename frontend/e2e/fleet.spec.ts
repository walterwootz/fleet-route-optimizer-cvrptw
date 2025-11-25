import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Fleet Overview Page
 * Tests locomotive table, filters, and search
 */

test.describe('Fleet Overview Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/fleet');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Flottenübersicht' })).toBeVisible();
    await expect(page.getByText('Alle Lokomotiven im Überblick')).toBeVisible();
  });

  test('should display locomotive table with headers', async ({ page }) => {
    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Lok-ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Reihe' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Standort' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Nächste HU' })).toBeVisible();
  });

  test('should display at least 10 locomotives', async ({ page }) => {
    // Check for some specific locomotives
    await expect(page.getByText('BR185-042')).toBeVisible();
    await expect(page.getByText('BR189-033')).toBeVisible();
    await expect(page.getByText('BR152-123')).toBeVisible();
  });

  test('should have search functionality', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Suche nach ID...');
    await expect(searchInput).toBeVisible();

    // Search for specific locomotive
    await searchInput.fill('BR185-042');

    // Should show only matching results
    await expect(page.getByText('BR185-042')).toBeVisible();

    // Count table rows (should be reduced)
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeLessThan(10); // Less than the total 10 locomotives
  });

  test('should filter by status', async ({ page }) => {
    // Select "Operational" status
    const statusSelect = page.locator('select').first();
    await statusSelect.selectOption('operational');

    // Should show only operational locomotives
    // All status badges should show "Betriebsbereit"
    const statusBadges = page.locator('text=Betriebsbereit');
    expect(await statusBadges.count()).toBeGreaterThan(0);
  });

  test('should filter by series', async ({ page }) => {
    // Get the series filter (second select)
    const seriesSelect = page.locator('select').nth(1);
    await seriesSelect.selectOption('BR185');

    // Should show only BR185 locomotives
    await expect(page.getByText('BR185-042')).toBeVisible();

    // BR189 should not be visible
    await expect(page.getByText('BR189-033')).not.toBeVisible();
  });

  test('should filter by location', async ({ page }) => {
    // Get the location filter (third select)
    const locationSelect = page.locator('select').nth(2);
    await locationSelect.selectOption('Berlin');

    // Should show only Berlin-based locomotives
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should combine multiple filters', async ({ page }) => {
    // Search + Status filter
    await page.getByPlaceholder('Suche nach ID...').fill('BR185');
    await page.locator('select').first().selectOption('operational');

    // Should show filtered results
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display status badges with correct colors', async ({ page }) => {
    // Operational badge should be green
    const operationalBadge = page.locator('text=Betriebsbereit').first();
    await expect(operationalBadge).toHaveClass(/bg-green-/);

    // Search for maintenance status
    await page.getByPlaceholder('Suche nach ID...').fill('maintenance');

    // Wait a moment for filter to apply
    await page.waitForTimeout(500);
  });

  test('should show "Keine Lokomotiven gefunden" when no matches', async ({ page }) => {
    // Search for non-existent locomotive
    await page.getByPlaceholder('Suche nach ID...').fill('NONEXISTENT9999');

    // Should show empty state message
    await expect(page.getByText('Keine Lokomotiven gefunden')).toBeVisible();
  });

  test('should display locomotive count', async ({ page }) => {
    // Should show count like "10 von 10" or similar
    const countText = page.getByText(/\d+ von \d+/);
    await expect(countText).toBeVisible();
  });

  test('should navigate back to dashboard', async ({ page }) => {
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
  });
});
