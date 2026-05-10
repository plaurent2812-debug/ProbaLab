import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const URL = process.env.VITE_SUPABASE_URL ?? '';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? '';

if (!URL || !SERVICE_KEY) {
  throw new Error(
    'E2E requires VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars set in your shell.'
  );
}

const admin: SupabaseClient = createClient(URL, SERVICE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

export interface TestUser {
  id: string;
  email: string;
  password: string;
}

export async function createTestUser(): Promise<TestUser> {
  const id = crypto.randomUUID();
  const email = `e2e-${id}@probalab-test.local`;
  const password = `Test-${id}-!`;

  const { data, error } = await admin.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
  });
  if (error || !data.user) throw error ?? new Error('createUser returned no user');

  return { id: data.user.id, email, password };
}

export async function deleteTestUser(userId: string): Promise<void> {
  const { error } = await admin.auth.admin.deleteUser(userId);
  if (error) console.warn(`Failed to delete test user ${userId}:`, error.message);
}
