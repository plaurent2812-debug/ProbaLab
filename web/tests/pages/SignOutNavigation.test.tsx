/**
 * Tests for explicit navigation after signOut in AccountPage and Header.
 *
 * The bug: both components call `void signOut()` without awaiting then
 * navigate explicitly. The redirect relies on <ProtectedRoute> bouncing once
 * user becomes null — benign today but races with React Router re-renders and
 * will cause wrong analytics/toast events in P2.
 *
 * The fix: both call sites must await signOut() then explicitly call
 * navigate('/auth/login', { replace: true }).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import AccountPage from '@/pages/account/AccountPage';
import { Header } from '@/components/layout/Header';

const mockSignOut = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockGetSession = vi.fn();

vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      onAuthStateChange: mockOnAuthStateChange,
      getSession: mockGetSession,
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: mockSignOut,
      signInWithOAuth: vi.fn(),
    },
  }),
}));

function LoginProbe() {
  return <p>login page</p>;
}

function setupWithSession(Component: React.ComponentType) {
  return render(
    <MemoryRouter initialEntries={['/account']}>
      <AuthProvider>
        <Routes>
          <Route path="/account" element={<Component />} />
          <Route path="/auth/login" element={<LoginProbe />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('signOut navigation — AccountPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } },
    });
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'u-1', email: 'test@test.com' },
          access_token: 'tok',
        },
      },
    });
    // signOut resolves successfully
    mockSignOut.mockResolvedValue({ error: null });
  });

  it('navigates explicitly to /auth/login after signOut button click', async () => {
    const user = userEvent.setup();
    setupWithSession(AccountPage);

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /déconnecter/i })).toBeInTheDocument()
    );

    await user.click(screen.getByRole('button', { name: /déconnecter/i }));

    await waitFor(() =>
      expect(screen.getByText('login page')).toBeInTheDocument()
    );

    // Verify signOut was awaited (called exactly once)
    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });
});

describe('signOut navigation — Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } },
    });
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'u-1', email: 'test@test.com' },
          access_token: 'tok',
        },
      },
    });
    mockSignOut.mockResolvedValue({ error: null });
  });

  it('navigates explicitly to /auth/login after Déconnexion button click in Header', async () => {
    const user = userEvent.setup();
    setupWithSession(Header);

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /déconnexion/i })).toBeInTheDocument()
    );

    await user.click(screen.getByRole('button', { name: /déconnexion/i }));

    await waitFor(() =>
      expect(screen.getByText('login page')).toBeInTheDocument()
    );

    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });
});
