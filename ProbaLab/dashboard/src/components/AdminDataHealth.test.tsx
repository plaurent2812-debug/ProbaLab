import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AdminDataHealth from './AdminDataHealth';

// Mock supabase.auth so the component renders without a real session.
vi.mock('@/lib/auth', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(async () => ({ data: { session: { access_token: 'fake-jwt' } } })),
    },
  },
}));

describe('AdminDataHealth', () => {
  beforeEach(() => {
    global.fetch = vi.fn() as unknown as typeof fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function mockFetchResponse(body: unknown, status = 200) {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: status < 400,
      status,
      json: async () => body,
    });
  }

  it('renders a heading mentioning data health', async () => {
    mockFetchResponse({
      generated_at: '2026-05-10T18:00:00Z',
      window_hours: 24,
      provider_failures: [],
      summary: { total_failures: 0, by_provider: {} },
    });

    render(<AdminDataHealth />);

    expect(
      await screen.findByRole('heading', { level: 2, name: /data health/i }),
    ).toBeInTheDocument();
  });

  it('displays "0 failures" when the endpoint returns an empty summary', async () => {
    mockFetchResponse({
      generated_at: '2026-05-10T18:00:00Z',
      window_hours: 24,
      provider_failures: [],
      summary: { total_failures: 0, by_provider: {} },
    });

    render(<AdminDataHealth />);

    await waitFor(() => {
      expect(screen.getByTestId('data-health-total-failures')).toHaveTextContent('0');
    });
  });

  it('lists each provider with its failure count', async () => {
    mockFetchResponse({
      generated_at: '2026-05-10T18:00:00Z',
      window_hours: 24,
      provider_failures: [
        {
          id: 1,
          recorded_at: '2026-05-10T17:30:00Z',
          provider: 'api_football',
          sport: 'football',
          endpoint: '/fixtures',
          status_code: 500,
          row_count: 0,
          is_success: false,
          error: 'HTTP 500',
        },
      ],
      summary: {
        total_failures: 3,
        by_provider: {
          api_football: { failure_count: 2 },
          the_odds_api: { failure_count: 1 },
        },
      },
    });

    render(<AdminDataHealth />);

    await waitFor(() => {
      // Both providers appear (api_football is also in the failures table).
      expect(screen.getAllByText(/api_football/i).length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getByText(/the_odds_api/i)).toBeInTheDocument();
    expect(screen.getByTestId('data-health-total-failures')).toHaveTextContent('3');
  });

  it('displays a fallback message when fetch fails', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('network down'));

    render(<AdminDataHealth />);

    await waitFor(() => {
      expect(screen.getByText(/indisponible/i)).toBeInTheDocument();
    });
  });

  it('shows the window in the heading', async () => {
    mockFetchResponse({
      generated_at: '2026-05-10T18:00:00Z',
      window_hours: 48,
      provider_failures: [],
      summary: { total_failures: 0, by_provider: {} },
    });

    render(<AdminDataHealth />);

    await waitFor(() => {
      expect(screen.getByText(/48\s*h/i)).toBeInTheDocument();
    });
  });
});
