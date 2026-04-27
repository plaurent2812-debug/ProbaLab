import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'jest-axe';
import { HeaderV2 } from './HeaderV2';

describe('HeaderV2', () => {
  it('renders logo and nav links on desktop', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    expect(screen.getByRole('link', { name: /probalab/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /accueil/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /matchs/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /compte/i })).toBeInTheDocument();
  });

  it('renders a premium sport-intelligence brand block instead of a plain text logo', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );

    expect(screen.getByTestId('header-brand-mark')).toHaveTextContent('P');
    expect(screen.getByText(/analyses & probabilités/i)).toBeInTheDocument();
  });

  it('uses a pill navigation group with an active visual state', () => {
    render(
      <MemoryRouter initialEntries={['/matchs']}>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );

    expect(screen.getByTestId('header-nav-pill-group')).toBeInTheDocument();
    const matchs = screen.getByRole('link', { name: /^matchs$/i });
    expect(matchs).toHaveAttribute('aria-current', 'page');
    expect(matchs).toHaveAttribute('data-active', 'true');
  });

  it('shows a conversion CTA for free users', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );

    const cta = screen.getByRole('link', { name: /passer premium/i });
    expect(cta).toHaveAttribute('href', '/premium');
  });

  it('shows admin access only for admin users', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="admin" />
      </MemoryRouter>
    );

    const admin = screen.getByRole('link', { name: /^admin$/i });
    expect(admin).toHaveAttribute('href', '/admin');
    expect(screen.queryByRole('link', { name: /passer premium/i })).not.toBeInTheDocument();
  });

  it('does not show admin access for non-admin users', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="premium" />
      </MemoryRouter>
    );

    expect(screen.queryByRole('link', { name: /^admin$/i })).not.toBeInTheDocument();
  });

  it('shows Free badge when userRole is free', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    expect(screen.getByText('Free')).toBeInTheDocument();
  });

  it('shows Trial J-X badge when userRole is trial', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="trial" trialDaysLeft={12} />
      </MemoryRouter>
    );
    expect(screen.getByText(/trial j-12/i)).toBeInTheDocument();
  });

  it('shows Premium badge when userRole is premium', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="premium" />
      </MemoryRouter>
    );
    expect(screen.getByText('Premium')).toBeInTheDocument();
  });

  it('hides horizontal nav on mobile (< md) via responsive classes', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const nav = screen.getByRole('navigation', { name: /navigation$/i });
    expect(nav.className).toMatch(/hidden/);
    expect(nav.className).toMatch(/md:flex/);
  });

  it('hides role badge on mobile (< md) via responsive classes', () => {
    render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const badge = screen.getByLabelText(/statut : free/i);
    expect(badge.className).toMatch(/hidden/);
    expect(badge.className).toMatch(/md:/);
  });

  it('marks Accueil as current page when on /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const accueilLinks = screen.getAllByRole('link', { name: /accueil/i });
    // The nav link (not the logo) should be aria-current
    const current = accueilLinks.find((l) => l.getAttribute('aria-current') === 'page');
    expect(current).toBeDefined();
    const matchs = screen.getByRole('link', { name: /^matchs$/i });
    expect(matchs).not.toHaveAttribute('aria-current');
  });

  it('marks Matchs as current page when on /matchs', () => {
    render(
      <MemoryRouter initialEntries={['/matchs']}>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const matchs = screen.getByRole('link', { name: /^matchs$/i });
    expect(matchs).toHaveAttribute('aria-current', 'page');
  });

  it('marks Matchs as current page on nested /matchs/123', () => {
    render(
      <MemoryRouter initialEntries={['/matchs/123']}>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const matchs = screen.getByRole('link', { name: /^matchs$/i });
    expect(matchs).toHaveAttribute('aria-current', 'page');
  });

  it('marks Compte as current page when on /compte', () => {
    render(
      <MemoryRouter initialEntries={['/compte']}>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const compte = screen.getByRole('link', { name: /^compte$/i });
    expect(compte).toHaveAttribute('aria-current', 'page');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <HeaderV2 userRole="free" />
      </MemoryRouter>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
