import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { RecoCard } from './RecoCard';
import type { Recommendation } from '../../../types/v2/match-detail';

const reco: Recommendation = {
  market_key: '1x2.home',
  market_label: 'Victoire Nice',
  odds: 2.1,
  confidence: 0.74,
  kelly_fraction: 0.035,
  edge: 0.08,
  book_name: 'Unibet',
};

describe('RecoCard', () => {
  it('renders the reco label', () => {
    render(<RecoCard recommendation={reco} />);
    expect(screen.getByText('Victoire Nice')).toBeInTheDocument();
  });

  it('renders the odds hero with 34px class', () => {
    render(<RecoCard recommendation={reco} />);
    const hero = screen.getByTestId('reco-odds');
    expect(hero.className).toMatch(/text-\[34px\]/);
    expect(hero).toHaveTextContent('2.10');
  });

  it('renders the breakdown with bettor-friendly labels', () => {
    render(<RecoCard recommendation={reco} />);
    expect(screen.getByText(/Confiance/i)).toBeInTheDocument();
    expect(screen.getByText(/Mise prudente/i)).toBeInTheDocument();
    expect(screen.getByText(/Signal/i)).toBeInTheDocument();
    expect(screen.getByText(/74%/)).toBeInTheDocument();
    expect(screen.getByText(/3\.5%/)).toBeInTheDocument();
    expect(screen.getByText(/\+8%/)).toBeInTheDocument();
    expect(screen.queryByText(/Kelly/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Edge/i)).not.toBeInTheDocument();
  });

  it('renders the source book name', () => {
    render(<RecoCard recommendation={reco} />);
    expect(screen.getByText(/Unibet/)).toBeInTheDocument();
  });

  it('returns null when recommendation is null', () => {
    const { container } = render(<RecoCard recommendation={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('accepts a custom data-testid on the root', () => {
    render(<RecoCard recommendation={reco} data-testid="reco-root" />);
    expect(screen.getByTestId('reco-root')).toBeInTheDocument();
  });

  it('exposes aria-label summarising the recommendation', () => {
    render(<RecoCard recommendation={reco} />);
    expect(
      screen.getByLabelText(/Recommandation.*Victoire Nice/i),
    ).toBeInTheDocument();
  });

  it('uses Sport Intelligence recommended pick styling', () => {
    render(<RecoCard recommendation={reco} />);
    const section = screen.getByTestId('reco-card');
    expect(section.className).toMatch(/rounded-\[22px\]/);
    expect(section.getAttribute('style')).toContain('rgba(96, 165, 250, 0.22)');
    expect(screen.getByText(/prono recommandé/i)).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<RecoCard recommendation={reco} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
