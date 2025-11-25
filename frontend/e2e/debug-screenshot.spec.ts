import { test } from '@playwright/test';

test('debug dashboard content', async ({ page }) => {
  // Capture console messages and errors
  const consoleMessages: string[] = [];
  const errors: string[] = [];

  page.on('console', msg => {
    consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', err => {
    errors.push(err.message);
  });

  console.log('=== NAVIGATING TO PAGE ===');
  await page.goto('/', { waitUntil: 'networkidle' });

  console.log('=== PAGE LOADED ===');

  // Wait a bit for React to render
  await page.waitForTimeout(2000);

  console.log('\n=== CONSOLE MESSAGES ===');
  if (consoleMessages.length > 0) {
    consoleMessages.forEach(msg => console.log(msg));
  } else {
    console.log('No console messages');
  }

  console.log('\n=== PAGE ERRORS ===');
  if (errors.length > 0) {
    errors.forEach(err => console.log('ERROR:', err));
  } else {
    console.log('No page errors');
  }

  // Get page info
  const title = await page.title();
  const rootDiv = await page.locator('#root').innerHTML();

  console.log('\n=== PAGE INFO ===');
  console.log('Title:', title);
  console.log('Root div innerHTML length:', rootDiv.length);
  console.log('Root div content (first 300 chars):', rootDiv.substring(0, 300));

  // Check for specific elements
  const hasTitle = await page.getByRole('heading', { name: /Dashboard/i }).count();
  const hasGesamtflotte = await page.getByText('Gesamtflotte').count();
  const hasLoks = await page.getByText(/25 Loks/).count();

  console.log('\n=== ELEMENT CHECKS ===');
  console.log('Headings with "Dashboard":', hasTitle);
  console.log('Text "Gesamtflotte":', hasGesamtflotte);
  console.log('Text "25 Loks":', hasLoks);
});
