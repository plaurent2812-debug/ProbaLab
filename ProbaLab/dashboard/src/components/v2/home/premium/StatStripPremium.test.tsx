import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatStripPremium } from './StatStripPremium';

describe('StatStripPremium', () => {
  it('uses public proof labels without finance or stats jargon', () => {
    render(<StatStripPremium />);

    expect(screen.getByText(/Performance publique/i)).toBeInTheDocument();
    expect(screen.getByText(/Signal marché/i)).toBeInTheDocument();
    expect(screen.getByText(/Précision 1X2/i)).toBeInTheDocument();
    expect(screen.getByText(/Capital simulé/i)).toBeInTheDocument();

    expect(screen.queryByText(/ROI/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Accuracy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Bankroll/i)).not.toBeInTheDocument();
  });
});
