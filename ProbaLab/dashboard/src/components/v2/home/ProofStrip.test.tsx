import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProofStrip } from './ProofStrip';

describe('ProofStrip', () => {
  it('renders the proof headline so users see the model is tracked continuously', () => {
    render(<ProofStrip />);

    // Headline must mention continuous tracking — proof-first language.
    expect(
      screen.getByText(/modèle suivi en continu/i),
    ).toBeInTheDocument();
  });

  it('explains that ROI, accuracy, Brier and bankroll are recalculated automatically', () => {
    render(<ProofStrip />);

    // The 4 KPIs from `usePerformanceSummary` must be named explicitly so
    // the user knows nothing is hand-edited.
    const body = screen.getByTestId('proof-strip-body');
    expect(body).toHaveTextContent(/roi 30j/i);
    expect(body).toHaveTextContent(/précision/i);
    expect(body).toHaveTextContent(/brier 7j/i);
    expect(body).toHaveTextContent(/bankroll/i);
    expect(body).toHaveTextContent(/automatiquement/i);
  });

  it('does not use guarantee or hype language (proof-first, not tipster)', () => {
    render(<ProofStrip />);

    // Forbidden words from the master plan: no profit promises, no hype.
    const root = screen.getByTestId('proof-strip');
    expect(root).not.toHaveTextContent(/garanti/i);
    expect(root).not.toHaveTextContent(/profit assuré/i);
    expect(root).not.toHaveTextContent(/jackpot/i);
    expect(root).not.toHaveTextContent(/sûr à 100/i);
  });

  it('shows the last update timestamp in UTC when provided', () => {
    render(<ProofStrip lastUpdateUtc="14:32" />);

    // Master plan: "last update UTC" must be visible to anchor freshness.
    expect(screen.getByText(/14:32 utc/i)).toBeInTheDocument();
  });

  it('falls back to a calm message when no timestamp is provided', () => {
    render(<ProofStrip />);

    // No raw "undefined" or "—" without context: user must understand
    // a refresh is in flight, not a failure.
    expect(screen.queryByText(/undefined/i)).not.toBeInTheDocument();
    expect(screen.getByTestId('proof-strip')).toBeInTheDocument();
  });

  it('exposes a single accessible region for screen readers', () => {
    render(<ProofStrip />);

    // The block carries trust messaging — must be reachable as one unit.
    expect(screen.getByRole('note')).toBeInTheDocument();
  });
});
