import { test, expect } from '@playwright/test';

test.describe('Parcours E2E Client - DEKOUWAY', () => {

  test('Page d accueil et consultation des annonces', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/DEKOUWAY/i);
    await expect(page.locator('h1')).toBeVisible();
  });

  test('Recherche de logements et filtres', async ({ page }) => {
    // La recherche par ville se fait depuis la barre héro de l'accueil (le
    // panneau de filtres de /annonces/ n'a pas de champ ville) ; `.last()`
    // cible le formulaire desktop visible (le formulaire mobile équivalent
    // est présent dans le DOM mais masqué en `md:hidden` à cette largeur).
    await page.goto('/');
    const cityInput = page.locator('input[name="city"]').last();
    await cityInput.fill('Dakar');
    await cityInput.press('Enter');
    await expect(page).toHaveURL(/city=Dakar/);
  });

  test('Interaction avec le Chatbot IA Groq', async ({ page }) => {
    await page.goto('/');
    // Le widget flottant est fermé par défaut (x-show sur $store.chat.open) :
    // il faut ouvrir le FAB avant que le champ de saisie ne soit interactif.
    await page.locator('[aria-label="Assistant IA DEKOUWAY"]').click();

    const question = 'Comment réserver un logement sur DEKOUWAY ?';
    const chatInput = page.locator('#floating-message-input');
    await expect(chatInput).toBeVisible();
    await chatInput.fill(question);
    await page.locator('#floating-chat-form button[type="submit"]').click();

    // Le message utilisateur n'apparaît dans #floating-chat-messages qu'après
    // un aller-retour HTMX réussi (POST vers /support/chat/ puis swap du
    // fragment serveur) : ce n'est donc pas juste une relecture de la saisie.
    const messages = page.locator('#floating-chat-messages');
    await expect(messages).toContainText(question, { timeout: 10000 });
    await expect(messages.locator('> div')).toHaveCount(3);
  });

});
