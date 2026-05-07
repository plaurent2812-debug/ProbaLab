/**
 * Tests for CallbackPage OAuth race condition fix.
 *
 * The bug: when `loading` flips to false but `user` is still null (because
 * Supabase hasn't finished processing the #access_token hash yet), the old
 * effect immediately navigated to /auth/login — kicking out just-authenticated
 * OAuth users.
 *
 * The fix: we must NOT navigate to /auth/login while the URL hash contains an
 * access_token fragment — only after SIGNED_IN fires or after we're sure there
 * is no token in the hash.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import CallbackPage from '@/pages/auth/CallbackPage';

// Collect all onAuthStateChange handlers (AuthProvider + CallbackPage both register one)
const authStateHandlers: Array<(event: string, session: unknown) => void> = [];

const mockOnAuthStateChange = vi.fn((handler: (event: string, session: unknown) => void) => {
  authStateHandlers.push(handler);
  return { data: { subscription: { unsubscribe: vi.fn() } } };
});
const mockGetSession = vi.fn();

vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      onAuthStateChange: mockOnAuthStateChange,
      getSession: mockGetSession,
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      signInWithOAuth: vi.fn(),
    },
  }),
}));

/** Fire event to all registered auth state handlers (simulates Supabase broadcast). */
function fireAuthStateChange(event: string, session: unknown) {
  for (const handler of authStateHandlers) {
    handler(event, session);
  }
}

function LoginProbe() {
  return <p>login page</p>;
}
function AccountProbe() {
  return <p>account page</p>;
}

function setup(initialPath = '/auth/callback') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/auth/callback" element={<CallbackPage />} />
          <Route path="/auth/login" element={<LoginProbe />} />
          <Route path="/account" element={<AccountProbe />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('CallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStateHandlers.length = 0;
  });

  it('does NOT redirect to /auth/login while session resolution is pending with a hash token', async () => {
    // Simulate slow getSession (never resolves during this test)
    mockGetSession.mockReturnValue(new Promise(() => {}));

    // Simulate hash with access_token present (OAuth redirect)
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '#access_token=eyJfake&token_type=bearer' },
      writable: true,
    });

    setup('/auth/callback#access_token=eyJfake&token_type=bearer');

    // Spinner should be visible — no redirect yet
    expect(screen.queryByText('login page')).not.toBeInTheDocument();

    // Even after a small tick, must NOT have redirected to login
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByText('login page')).not.toBeInTheDocument();

    // Reset hash
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '' },
      writable: true,
    });
  });

  it('redirects to /account after SIGNED_IN fires when hash has access_token', async () => {
    // Simulate hash with access_token present (OAuth redirect)
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '#access_token=eyJfake&token_type=bearer' },
      writable: true,
    });

    // getSession resolves with no session (hash not yet processed)
    mockGetSession.mockResolvedValue({ data: { session: null } });

    setup('/auth/callback#access_token=eyJfake&token_type=bearer');

    // Wait for AuthProvider to finish loading
    await waitFor(() => expect(authStateHandlers.length).toBeGreaterThan(0));

    // Simulate Supabase firing SIGNED_IN — this is what the real client does
    // after exchanging the #access_token fragment for a real session.
    act(() => {
      fireAuthStateChange('SIGNED_IN', {
        user: { id: 'u-oauth', email: 'oauth@test.com' },
        access_token: 'eyJfake',
      });
    });

    // Must land on /account, not /auth/login
    await waitFor(() =>
      expect(screen.getByText('account page')).toBeInTheDocument()
    );
    expect(screen.queryByText('login page')).not.toBeInTheDocument();

    // Reset hash
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '' },
      writable: true,
    });
  });

  it('redirects to /auth/login when loading resolves with no session and no hash', async () => {
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '' },
      writable: true,
    });

    mockGetSession.mockResolvedValue({ data: { session: null } });

    setup('/auth/callback');

    await waitFor(() =>
      expect(screen.getByText('login page')).toBeInTheDocument()
    );
  });

  it('redirects to /account when loading resolves with an existing session and no hash', async () => {
    Object.defineProperty(window, 'location', {
      value: { ...window.location, hash: '' },
      writable: true,
    });

    mockGetSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'u-existing', email: 'existing@test.com' },
          access_token: 'tok',
        },
      },
    });

    setup('/auth/callback');

    await waitFor(() =>
      expect(screen.getByText('account page')).toBeInTheDocument()
    );
  });
});
