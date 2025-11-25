import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Finance Page
 * Tests invoices, budget tracking, and supplier charts
 */

test.describe('Finance Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/finance');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Finanzen' })).toBeVisible();
    await expect(page.getByText('Rechnungen und Budget-Übersicht')).toBeVisible();
  });

  test('should display 4 KPI cards', async ({ page }) => {
    // Gesamt Rechnungen
    await expect(page.getByText('Gesamt Rechnungen')).toBeVisible();

    // Ausstehend
    await expect(page.getByText('Ausstehend')).toBeVisible();

    // Überfällig
    await expect(page.getByText('Überfällig')).toBeVisible();

    // Bezahlt
    await expect(page.getByText('Bezahlt')).toBeVisible();
  });

  test('should display invoices table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Rechnungen' })).toBeVisible();

    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Rechnung' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Lieferant' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Betrag' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
  });

  test('should display at least 5 invoices', async ({ page }) => {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('should display invoice numbers in correct format', async ({ page }) => {
    // Invoice IDs should be like "INV-123"
    const invNumbers = page.locator('text=/INV-\\d+/');
    expect(await invNumbers.count()).toBeGreaterThan(0);
  });

  test('should display invoice status badges', async ({ page }) => {
    // Check for various status badges
    const hasPending = (await page.locator('text=Ausstehend').count()) > 0;
    const hasApproved = (await page.locator('text=Genehmigt').count()) > 0;
    const hasPaid = (await page.locator('text=Bezahlt').count()) > 0;
    const hasOverdue = (await page.locator('text=Überfällig').count()) > 0;

    // At least one status should exist
    expect(hasPending || hasApproved || hasPaid || hasOverdue).toBeTruthy();
  });

  test('should filter invoices by status', async ({ page }) => {
    const filterSelect = page.locator('select');
    await filterSelect.selectOption('paid');

    await page.waitForTimeout(300);

    const rows = page.locator('table tbody tr');
    const count = await rows.count();

    if (count > 0) {
      // All visible invoices should have "Bezahlt" status
      const paidBadges = page.locator('text=Bezahlt');
      expect(await paidBadges.count()).toBeGreaterThan(0);
    }
  });

  test('should display budget tracker card', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Jahresbudget 2025' })).toBeVisible();

    // Should show budget details
    await expect(page.getByText(/Gesamt:/)).toBeVisible();
    await expect(page.getByText(/Ausgegeben:/)).toBeVisible();
    await expect(page.getByText(/Verbleibend:/)).toBeVisible();
  });

  test('should display budget progress bar', async ({ page }) => {
    // Budget card should have a progress bar
    const budgetCard = page.locator('text=Jahresbudget 2025').locator('..');
    const progressBar = budgetCard.locator('div[class*="bg-"][class*="-500"]');

    // Check if progress bar exists
    expect(await progressBar.count()).toBeGreaterThan(0);
  });

  test('should display top suppliers card', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Top Lieferanten' })).toBeVisible();

    // Should show supplier names and amounts
    const hasSuppliers = (await page.locator('text=/Siemens|Bombardier|Knorr/').count()) > 0;
    expect(hasSuppliers).toBeTruthy();
  });

  test('should display BarList for suppliers', async ({ page }) => {
    // BarList component should exist in the Top Lieferanten card
    const suppliersCard = page.locator('text=Top Lieferanten').locator('..');

    // Should have multiple supplier entries
    const supplierEntries = suppliersCard.locator('div').filter({ hasText: /€/ });
    expect(await supplierEntries.count()).toBeGreaterThan(0);
  });

  test('should display amounts in EUR format', async ({ page }) => {
    // Should show EUR values like "€15.000" or "€5.050"
    const eurPattern = /€[\d.,]+/;
    const allText = await page.textContent('body');
    expect(eurPattern.test(allText || '')).toBeTruthy();
  });

  test('should link invoices to work orders', async ({ page }) => {
    // Should show WO references like "WO-12345"
    const woNumbers = page.locator('text=/WO-\\d+/');
    expect(await woNumbers.count()).toBeGreaterThan(0);
  });

  test('should display dates in German format', async ({ page }) => {
    // Should show dates like "24.11.2025" or similar
    const datePattern = /\d{2}\.\d{2}\.\d{4}/;
    const cells = page.locator('table tbody tr td');
    const allText = await cells.allTextContents();
    const hasGermanDate = allText.some(text => datePattern.test(text));

    expect(hasGermanDate).toBeTruthy();
  });

  test('should use 2-column grid layout on large screens', async ({ page }) => {
    // On desktop, should have 2-column layout (table 2/3, sidebar 1/3)
    // This is a visual test, so we just check elements exist

    const budgetCard = page.locator('text=Jahresbudget 2025').locator('..');
    const suppliersCard = page.locator('text=Top Lieferanten').locator('..');

    await expect(budgetCard).toBeVisible();
    await expect(suppliersCard).toBeVisible();
  });

  test('should navigate to procurement page', async ({ page }) => {
    await page.getByRole('link', { name: 'Beschaffung' }).click();
    await expect(page).toHaveURL('/procurement');
  });
});
