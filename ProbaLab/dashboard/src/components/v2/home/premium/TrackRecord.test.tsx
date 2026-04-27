import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrackRecord } from './TrackRecord';

describe('TrackRecord', () => {
  it('explains public results without cherry-picking wording', () => {
    render(<TrackRecord />);

    expect(screen.getByText(/Gagnants et perdants/i)).toBeInTheDocument();
    expect(screen.getByText(/Pas de sélection favorable/i)).toBeInTheDocument();
    expect(screen.queryByText(/cherry-picking/i)).not.toBeInTheDocument();
  });
});
