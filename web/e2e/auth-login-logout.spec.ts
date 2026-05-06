import { test, expect } from '@playwright/test';
import { createTestUser, deleteTestUser, type TestUser } from './helpers/test-user';

test.describe('Login + logout flow', () => {
  let user: TestUser;

  test.beforeAll(async () => {
    user = await createTestUser();
  });

  test.afterAll(async () => {
    await deleteTestUser(user.id);
  });

  test('user can login with email/password, sees account, logs out', async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByLabel(/email/i).fill(user.email);
    await page.getByLabel(/mot de passe/i).fill(user.password);
    await page.getByRole('button', { name: /se connecter/i }).click();

    await expect(page).toHaveURL(/\/account$/, { timeout: 10_000 });
    await expect(page.getByRole('heading', { name: /mon compte/i })).toBeVisible();
    await expect(page.getByText(user.email)).toBeVisible();

    await page.getByRole('button', { name: /se déconnecter/i }).click();

    // After logout on /account, ProtectedRoute kicks back to /auth/login
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5_000 });
    await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
  });

  test('protected route redirects unauthenticated user to login', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/account');
    await expect(page).toHaveURL(/\/auth\/login\?next=%2Faccount/, { timeout: 5_000 });
  });
});
