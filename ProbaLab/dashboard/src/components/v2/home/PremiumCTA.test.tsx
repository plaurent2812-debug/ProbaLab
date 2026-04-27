import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';
import { PremiumCTA } from './PremiumCTA';

expect.extend(toHaveNoViolations);

function wrap(ui: React.ReactElement) {
  return <MemoryRouter>{ui}</MemoryRouter>;
}

describe('PremiumCTA', () => {
  it('renders heading, price and CTA link to /premium', () => {
    render(wrap(<PremiumCTA />));
    expect(screen.getByText(/14,99/)).toBeInTheDocument();
    expect(screen.getByText(/suivi du capital/i)).toBeInTheDocument();
    expect(screen.queryByText(/bankroll/i)).not.toBeInTheDocument();
    const cta = screen.getByRole('link', { name: /Activer l'abonnement/i });
    expect(cta).toHaveAttribute('href', '/premium');
  });

  it('has no axe violations', async () => {
    const { container } = render(wrap(<PremiumCTA />));
    expect(await axe(container)).toHaveNoViolations();
  });
});
