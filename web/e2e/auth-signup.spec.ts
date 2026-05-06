import { test, expect } from '@playwright/test';
import { deleteTestUser } from './helpers/test-user';

test.describe('Signup flow', () => {
  let createdUserId: string | null = null;

  test.afterEach(async () => {
    if (createdUserId) {
      await deleteTestUser(createdUserId);
      createdUserId = null;
    }
  });

  test('user can submit signup form and gets the confirmation message', async ({ page }) => {
    const id = crypto.randomUUID();
    const email = `e2e-${id}@probalab-test.local`;
    const password = `Test-${id}-!`;

    await page.goto('/auth/signup');
    await expect(page.getByRole('heading', { name: /créer un compte/i })).toBeVisible();

    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).fill(password);
    await page.getByRole('button', { name: /s'inscrire/i }).click();

    // Wait for confirmation status message
    await expect(page.getByRole('status')).toContainText(/vérifie tes emails/i, { timeout: 10_000 });

    // Cleanup: lookup user id by querying auth.users directly via service role.
    // Avoids listUsers() pagination (default 50/page, hard-capped server-side) which silently misses users on projects with many accounts.
    const { createClient } = await import('@supabase/supabase-js');
    const admin = createClient(
      process.env.VITE_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      { auth: { autoRefreshToken: false, persistSession: false } }
    );
    const { data } = await admin
      .schema('auth' as never)
      .from('users')
      .select('id')
      .eq('email', email)
      .maybeSingle();
    if (data) createdUserId = (data as { id: string }).id;
  });
});
