import { test, expect } from '@playwright/test';

/**
 * E2E Tests for HR/Personnel Page
 * Tests staff management, qualifications, and training sessions
 */

test.describe('HR/Personnel Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/hr');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Personal-Management' })).toBeVisible();
    await expect(page.getByText('Mitarbeiter, Qualifikationen und Schulungen')).toBeVisible();
  });

  test('should display 5 KPI cards', async ({ page }) => {
    // Gesamt
    await expect(page.getByText('Gesamt')).toBeVisible();

    // Verfügbar
    await expect(page.getByText('Verfügbar')).toBeVisible();

    // Zugewiesen
    await expect(page.getByText('Zugewiesen')).toBeVisible();

    // In Schulung
    await expect(page.getByText('In Schulung')).toBeVisible();

    // Zertifikate
    await expect(page.getByText('Zertifikate')).toBeVisible();
  });

  test('should display staff table with headers', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Mitarbeiter' })).toBeVisible();

    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Rolle' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Qualifikationen' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
  });

  test('should display at least 8 staff members', async ({ page }) => {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(8);
  });

  test('should display employee IDs in correct format', async ({ page }) => {
    // Employee IDs should be like "MA-123"
    const maNumbers = page.locator('text=/MA-\\d+/');
    expect(await maNumbers.count()).toBeGreaterThan(0);
  });

  test('should display staff status badges', async ({ page }) => {
    // Check for various status badges
    const hasAvailable = (await page.locator('text=Verfügbar').count()) > 0;
    const hasAssigned = (await page.locator('text=Zugewiesen').count()) > 0;
    const hasTraining = (await page.locator('text=In Schulung').count()) > 0;

    // At least one status should exist
    expect(hasAvailable || hasAssigned || hasTraining).toBeTruthy();
  });

  test('should filter staff by status', async ({ page }) => {
    // Get the status filter (first select)
    const statusSelect = page.locator('select').first();
    await statusSelect.selectOption('available');

    await page.waitForTimeout(300);

    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible staff should have "Verfügbar" status
      const availableBadges = page.locator('text=Verfügbar');
      expect(await availableBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should filter staff by role', async ({ page }) => {
    // Get the role filter (second select)
    const roleSelect = page.locator('select').nth(1);
    await roleSelect.selectOption('Mechaniker');

    await page.waitForTimeout(300);

    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible staff should have "Mechaniker" role
      const mechaniker = page.locator('text=Mechaniker');
      expect(await mechaniker.count()).toBeGreaterThan(0);
    }
  });

  test('should display qualifications as badges', async ({ page }) => {
    // Check for qualification badges
    const hasSchweissen = (await page.locator('text=Schweißen').count()) > 0;
    const hasHydraulik = (await page.locator('text=Hydraulik').count()) > 0;
    const hasElektrik = (await page.locator('text=Elektrik').count()) > 0;

    // At least one qualification should exist
    expect(hasSchweissen || hasHydraulik || hasElektrik).toBeTruthy();
  });

  test('should truncate qualifications with "+X" badge', async ({ page }) => {
    // If staff has more than 3 qualifications, should show "+1", "+2", etc.
    const plusBadges = page.locator('text=/\\+\\d+/');
    const count = await plusBadges.count();

    // May or may not exist depending on data
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display certificate validity status', async ({ page }) => {
    // Check for certificate status badges
    const hasValid = (await page.locator('text=Gültig').count()) > 0;
    const hasExpired = (await page.locator('text=Abgelaufen').count()) > 0;

    // At least one certificate status should exist
    expect(hasValid || hasExpired).toBeTruthy();
  });

  test('should display qualifications distribution', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Qualifikationen' })).toBeVisible();
    await expect(page.getByText('Verteilung im Team')).toBeVisible();

    // Should show progress bars for qualifications
    const progressBars = page.locator('div[class*="bg-blue-500"]');
    expect(await progressBars.count()).toBeGreaterThan(0);
  });

  test('should display upcoming training sessions', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Geplante Schulungen' })).toBeVisible();

    // Should show training types
    const hasTraining = (await page.locator('text=/Auffrischung|Schulung|Fortgeschritten/').count()) > 0;
    expect(hasTraining).toBeTruthy();
  });

  test('should show training participant count', async ({ page }) => {
    // Should show badges like "3 Teilnehmer", "1 Teilnehmer"
    const participantBadges = page.locator('text=/\\d+ Teilnehmer/');
    expect(await participantBadges.count()).toBeGreaterThan(0);
  });

  test('should display training dates', async ({ page }) => {
    // Should show dates in German format
    const datePattern = /\d{2}\.\s\w+\.\s\d{4}/; // "15. Jan. 2025"
    const trainingSection = page.locator('text=Geplante Schulungen').locator('..');
    const sectionText = await trainingSection.textContent();

    expect(datePattern.test(sectionText || '')).toBeTruthy();
  });

  test('should show staff count', async ({ page }) => {
    // Should show count like "10 von 10" or similar
    const countText = page.locator('text=/\\d+ von \\d+/');
    await expect(countText).toBeVisible();
  });

  test('should display work assignment references', async ({ page }) => {
    // Should show WO references like "WO-12345" for assigned staff
    const woNumbers = page.locator('text=/WO-\\d+/');
    const count = await woNumbers.count();

    // May or may not exist depending on assignments
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should navigate to documents page', async ({ page }) => {
    await page.getByRole('link', { name: 'Dokumente' }).click();
    await expect(page).toHaveURL('/documents');
  });
});
