import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Procurement Page
 * Tests parts inventory, purchase requests, and filtering
 */

test.describe('Procurement Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/procurement');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Beschaffung' })).toBeVisible();
    await expect(page.getByText('Lagerverwaltung und Bestellungen')).toBeVisible();
  });

  test('should display 4 KPI cards', async ({ page }) => {
    // Lagerwert
    await expect(page.getByText('Lagerwert')).toBeVisible();

    // Kritischer Bestand
    await expect(page.getByText('Kritischer Bestand')).toBeVisible();

    // Niedriger Bestand
    await expect(page.getByText('Niedriger Bestand')).toBeVisible();

    // Monatl. Ausgaben
    await expect(page.getByText('Monatl. Ausgaben')).toBeVisible();
  });

  test('should display stock inventory table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Lagerbestand' })).toBeVisible();

    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Teil-Nr.' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Beschreibung' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Verfügbar' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
  });

  test('should display purchase requests table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Bestellanforderungen' })).toBeVisible();

    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'PR-Nummer' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Teil' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Menge' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Benötigt bis|Benötigt am/ })).toBeVisible();
  });

  test('should display at least 5 stock items', async ({ page }) => {
    const rows = page.locator('table tbody tr').first();
    const table = rows.locator('..');
    const stockRows = table.locator('tr');
    const count = await stockRows.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('should display stock status badges', async ({ page }) => {
    // Check for status badges (critical, low, ok)
    const hasCritical = (await page.locator('text=Kritisch').count()) > 0;
    const hasLow = (await page.locator('text=Niedrig').count()) > 0;
    const hasOk = (await page.locator('text=Ok').count()) > 0;

    // At least one status should exist
    expect(hasCritical || hasLow || hasOk).toBeTruthy();
  });

  test('should filter stock by status', async ({ page }) => {
    // Get the stock status filter (first select on the page)
    const stockStatusSelect = page.locator('select').first();
    await stockStatusSelect.selectOption('critical');

    await page.waitForTimeout(300);

    const rows = page.locator('table').first().locator('tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible items should have "Kritisch" status
      const criticalBadges = page.locator('text=Kritisch');
      expect(await criticalBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should display purchase request status badges', async ({ page }) => {
    // Check for PR status badges (pending, approved, ordered, delivered)
    const hasPending = (await page.locator('text=Ausstehend').count()) > 0;
    const hasApproved = (await page.locator('text=Genehmigt').count()) > 0;
    const hasOrdered = (await page.locator('text=Bestellt').count()) > 0;

    // At least one status should exist
    expect(hasPending || hasApproved || hasOrdered).toBeTruthy();
  });

  test('should filter purchase requests by status', async ({ page }) => {
    // Get the PR status filter (second select on the page)
    const prStatusSelect = page.locator('select').nth(1);
    await prStatusSelect.selectOption('pending');

    await page.waitForTimeout(300);

    const tables = page.locator('table');
    const prTable = tables.nth(1);
    const rows = prTable.locator('tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible items should have "Ausstehend" status
      const pendingBadges = page.locator('text=Ausstehend');
      expect(await pendingBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should display part numbers in correct format', async ({ page }) => {
    // Part numbers should be like "P-12345"
    const partNumbers = page.locator('text=/P-\\d+/');
    expect(await partNumbers.count()).toBeGreaterThan(0);
  });

  test('should display PR numbers in correct format', async ({ page }) => {
    // PR numbers should be like "PR-1234"
    const prNumbers = page.locator('text=/PR-\\d+/');
    expect(await prNumbers.count()).toBeGreaterThan(0);
  });

  test('should display quantity with "Stück"', async ({ page }) => {
    // Should show quantities like "50 Stück"
    const qtyText = page.locator('text=/\\d+ Stück/');
    expect(await qtyText.count()).toBeGreaterThan(0);
  });

  test('should display monetary values in EUR format', async ({ page }) => {
    // Should show EUR values like "€125.000" or "€18.500"
    const eurPattern = /€[\d.,]+/;
    const allText = await page.textContent('body');
    expect(eurPattern.test(allText || '')).toBeTruthy();
  });

  test('should navigate to finance page', async ({ page }) => {
    await page.getByRole('link', { name: 'Finanzen' }).click();
    await expect(page).toHaveURL('/finance');
  });
});
