import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider } from '@/contexts/AuthContext';
import { useAuth } from '@/hooks/useAuth';

const mockOnAuthStateChange = vi.fn();
const mockGetSession = vi.fn();
const mockSignInWithPassword = vi.fn();
const mockSignUp = vi.fn();
const mockSignOut = vi.fn();
const mockSignInWithOAuth = vi.fn();

vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      onAuthStateChange: mockOnAuthStateChange,
      getSession: mockGetSession,
      signInWithPassword: mockSignInWithPassword,
      signUp: mockSignUp,
      signOut: mockSignOut,
      signInWithOAuth: mockSignInWithOAuth,
    },
  }),
}));

function Probe() {
  const { user, loading } = useAuth();
  if (loading) return <p>loading</p>;
  return <p>{user ? `user:${user.id}` : 'anon'}</p>;
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
  });

  it('starts in loading state then resolves to anon when no session', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByText('loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('anon')).toBeInTheDocument());
  });

  it('exposes user when an existing session is present', async () => {
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'u-1', email: 'a@b.fr' },
          access_token: 'tok',
        },
      },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('user:u-1')).toBeInTheDocument());
  });

  it('updates state when onAuthStateChange fires SIGNED_IN', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    let cb: ((event: string, session: unknown) => void) | undefined;
    mockOnAuthStateChange.mockImplementation((handler) => {
      cb = handler;
      return { data: { subscription: { unsubscribe: vi.fn() } } };
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('anon')).toBeInTheDocument());

    act(() => {
      cb?.('SIGNED_IN', { user: { id: 'u-2', email: 'c@d.fr' }, access_token: 't' });
    });

    await waitFor(() => expect(screen.getByText('user:u-2')).toBeInTheDocument());
  });
});
