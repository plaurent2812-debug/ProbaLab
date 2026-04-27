import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'jest-axe';
import { MatchDecisionHero } from './MatchDecisionHero';
import type {
  MatchHeader,
  MarketProb,
  Recommendation,
} from '@/types/v2/match-detail';

const header: MatchHeader = {
  fixture_id: 'fx-1',
  kickoff_utc: '2026-04-27T19:00:00Z',
  league_name: 'Ligue 1',
  stadium: 'Parc des Princes',
  home: {
    id: 1,
    name: 'PSG',
    logo_url: '/psg.png',
    rank: 1,
    form: ['W', 'W', 'D', 'W', 'W'],
  },
  away: {
    id: 2,
    name: 'Lens',
    logo_url: '/lens.png',
    rank: 5,
    form: ['L', 'W', 'D', 'L', 'W'],
  },
};

const recommendation: Recommendation = {
  market_key: '1x2.home',
  market_label: 'PSG gagne',
  odds: 1.85,
  confidence: 0.74,
  kelly_fraction: 0.025,
  edge: 0.076,
  book_name: 'Betclic',
};

const recommendedMarket: MarketProb = {
  market_key: '1x2.home',
  label: 'PSG gagne',
  probability: 0.58,
  fair_odds: 1.72,
  best_book_odds: 1.85,
  is_value: true,
  edge: 0.076,
};

function renderHero(overrides?: Partial<React.ComponentProps<typeof MatchDecisionHero>>) {
  return render(
    <MemoryRouter>
      <MatchDecisionHero
        header={header}
        probs={{ home: 0.58, draw: 0.24, away: 0.18 }}
        recommendation={recommendation}
        recommendedMarket={recommendedMarket}
        analysisAvailable
        {...overrides}
      />
    </MemoryRouter>,
  );
}

describe('MatchDecisionHero', () => {
  it('renders a premium decision-first summary', () => {
    renderHero();

    expect(screen.getByTestId('match-decision-hero')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /décision du match/i })).toBeInTheDocument();
    expect(screen.getByText(/Probabilités clés/i)).toBeInTheDocument();
    expect(screen.getByText('À surveiller')).toBeInTheDocument();
    expect(screen.getByText(/Prono recommandé/i)).toBeInTheDocument();
    expect(screen.getByText(/PSG gagne/i)).toBeInTheDocument();
    expect(screen.getByText(/1\.85/)).toBeInTheDocument();
  });

  it('exposes quick links to analysis and markets', () => {
    renderHero();

    expect(screen.getByRole('link', { name: /voir l'analyse/i })).toHaveAttribute(
      'href',
      '#analyse-ia',
    );
    expect(screen.getByRole('link', { name: /tous les marchés/i })).toHaveAttribute(
      'href',
      '#marches',
    );
  });

  it('keeps the hero useful when no pick is recommended', () => {
    renderHero({ recommendation: null, recommendedMarket: null });

    expect(screen.getByText(/Aucun prono recommandé/i)).toBeInTheDocument();
    expect(screen.getByText(/Le modèle ne force pas de pari/i)).toBeInTheDocument();
  });

  it('has no axe violations', async () => {
    const { container } = renderHero();
    expect(await axe(container)).toHaveNoViolations();
  });
});
