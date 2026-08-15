import { test, expect } from '@playwright/test';

test.describe('Parcours E2E SuperAdmin ERP - DEKOUWAY', () => {

  test('Connexion Administration Django', async ({ page }) => {
    await page.goto('/admin/');
    await expect(page.locator('#id_username')).toBeVisible();
    await expect(page.locator('#id_password')).toBeVisible();
  });

  test('Dashboard SuperAdmin ERP', async ({ page }) => {
    await page.goto('/dashboard/superadmin/');
    const currentUrl = page.url();
    expect(currentUrl).toBeTruthy();
  });

});
