import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/shared/ProtectedRoute';

const mockOnAuthStateChange = vi.fn();
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

beforeEach(() => {
  vi.clearAllMocks();
  mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
});

function setup(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/auth/login" element={<p>login page</p>} />
          <Route
            path="/account"
            element={
              <ProtectedRoute>
                <p>account content</p>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  it('renders children when user is authenticated', async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { user: { id: 'u-1', email: 'a@b.fr' }, access_token: 't' } },
    });

    setup('/account');
    await waitFor(() => expect(screen.getByText('account content')).toBeInTheDocument());
  });

  it('redirects to /auth/login when user is anonymous', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    setup('/account');
    await waitFor(() => expect(screen.getByText('login page')).toBeInTheDocument());
  });
});
