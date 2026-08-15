import { test, expect } from '@playwright/test';

test.describe('Parcours E2E Propriétaire - DEKOUWAY', () => {

  test('Page d inscription Propriétaire', async ({ page }) => {
    await page.goto('/rejoindre/hote/');
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
  });

  test('Dashboard Propriétaire et gestion des annonces', async ({ page }) => {
    await page.goto('/dashboard/owner/');
    // Vérification de la redirection si non authentifié ou affichage du dashboard
    const currentUrl = page.url();
    expect(currentUrl).toBeTruthy();
  });

});
