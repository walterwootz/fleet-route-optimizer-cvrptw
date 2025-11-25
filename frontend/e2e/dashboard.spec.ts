import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Dashboard Page
 * Tests KPIs, charts, and navigation
 */

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display page title and description', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByText('Übersicht der Flottenstatistiken')).toBeVisible();
  });

  test('should display all 4 KPI cards', async ({ page }) => {
    // Gesamt Loks
    await expect(page.getByText('Gesamt Loks')).toBeVisible();
    await expect(page.getByText('25')).toBeVisible();

    // Verfügbarkeit
    await expect(page.getByText('Verfügbarkeit')).toBeVisible();
    await expect(page.getByText('92.5%')).toBeVisible();

    // In Wartung
    await expect(page.getByText('In Wartung')).toBeVisible();
    await expect(page.getByText('3')).toBeVisible();

    // Überfällig
    await expect(page.getByText('HU Überfällig')).toBeVisible();
    await expect(page.getByText('2')).toBeVisible();
  });

  test('should display Flottenverteilung DonutChart', async ({ page }) => {
    await expect(page.getByText('Flottenverteilung')).toBeVisible();
    await expect(page.getByText('Nach Status')).toBeVisible();

    // Check legend items
    await expect(page.getByText('Operational')).toBeVisible();
    await expect(page.getByText('Maintenance')).toBeVisible();
    await expect(page.getByText('Out of Service')).toBeVisible();
  });

  test('should display Verfügbarkeit BarChart', async ({ page }) => {
    await expect(page.getByText('Verfügbarkeit nach Reihe')).toBeVisible();

    // Check some series names
    await expect(page.getByText('BR185')).toBeVisible();
    await expect(page.getByText('BR189')).toBeVisible();
    await expect(page.getByText('BR152')).toBeVisible();
  });

  test('should have working sidebar navigation', async ({ page }) => {
    // Navigate to Flotte
    await page.getByRole('link', { name: 'Flotte' }).click();
    await expect(page).toHaveURL('/fleet');

    // Navigate back to Dashboard
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
  });

  test('should highlight active navigation item', async ({ page }) => {
    const dashboardLink = page.getByRole('link', { name: 'Dashboard' });

    // Dashboard link should have active styling
    await expect(dashboardLink).toHaveClass(/bg-blue-50/);
  });

  test('should display FLEET-ONE button', async ({ page }) => {
    // Check for F1 button (FLEET-ONE toggle)
    const fleetOneButton = page.locator('button').filter({ hasText: 'F1' });
    await expect(fleetOneButton).toBeVisible();
  });
});
