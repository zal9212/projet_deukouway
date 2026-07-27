import { test, expect } from '@playwright/test';

test.describe('Parcours E2E Client - DEKOUWAY', () => {

  test('Page d accueil et consultation des annonces', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/DEKOUWAY/i);
    await expect(page.locator('h1')).toBeVisible();
  });

  test('Recherche de logements et filtres', async ({ page }) => {
    await page.goto('/properties/');
    await page.fill('input[name="city"]', 'Dakar');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/city=Dakar/);
  });

  test('Interaction avec le Chatbot IA Groq', async ({ page }) => {
    await page.goto('/');
    const chatInput = page.locator('#chatbot-input');
    if (await chatInput.isVisible()) {
      await chatInput.fill('Comment réserver un logement sur DEKOUWAY ?');
      await page.click('#chatbot-send-btn');
      await expect(page.locator('.chat-message-assistant')).toBeVisible({ timeout: 10000 });
    }
  });

});
