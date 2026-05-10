import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getSupabase } from '@/lib/supabase';
import { FullPageSpinner } from '@/components/shared/LoadingSpinner';

/**
 * OAuth callback landing page.
 *
 * Race condition guard: with `detectSessionInUrl: true`, Supabase processes the
 * #access_token fragment asynchronously. If we navigate to /auth/login the
 * moment `loading` flips to false (before the SIGNED_IN event fires), we kick
 * out a legitimately authenticated OAuth user.
 *
 * Strategy:
 *  - If the URL hash contains `access_token`, wait for a SIGNED_IN event from
 *    onAuthStateChange before deciding where to redirect. This gives Supabase
 *    time to exchange the token and populate the session.
 *  - If there is no token in the hash, fall back to the current auth context
 *    state (fast path for direct navigations to /auth/callback).
 */
export default function CallbackPage() {
  const { loading, user } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [hasHashToken] = useState(() =>
    window.location.hash.includes('access_token')
  );

  // Listen for SIGNED_IN so we can safely redirect OAuth users.
  useEffect(() => {
    if (!hasHashToken) return;

    const supabase = getSupabase();
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          const next = params.get('next') ?? '/account';
          navigate(next, { replace: true });
        }
      }
    );

    return () => subscription.unsubscribe();
  }, [hasHashToken, navigate, params]);

  // Fast path: no hash token → use auth context directly once resolved.
  useEffect(() => {
    if (hasHashToken) return;
    if (loading) return;

    const next = params.get('next') ?? '/account';
    navigate(user ? next : '/auth/login', { replace: true });
  }, [hasHashToken, loading, user, navigate, params]);

  return <FullPageSpinner />;
}
