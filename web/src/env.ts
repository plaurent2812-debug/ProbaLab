import { z } from 'zod';

export const envSchema = z.object({
  VITE_SUPABASE_URL: z.string().url(),
  VITE_SUPABASE_ANON_KEY: z.string().min(10),
  VITE_API_URL: z.string().url(),
});

export type Env = z.infer<typeof envSchema>;

let cachedEnv: Env | null = null;

export function validateEnv(): Env {
  if (cachedEnv) return cachedEnv;
  const result = envSchema.safeParse(import.meta.env);
  if (!result.success) {
    const message = `Invalid frontend env vars:\n${JSON.stringify(result.error.flatten().fieldErrors, null, 2)}`;
    throw new Error(message);
  }
  cachedEnv = result.data;
  return cachedEnv;
}
