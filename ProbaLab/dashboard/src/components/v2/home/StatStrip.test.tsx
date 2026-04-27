import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { StatStrip } from './StatStrip';
import type { PerformanceSummary } from '@/types/v2/performance';

expect.extend(toHaveNoViolations);

const data: PerformanceSummary = {
  roi30d: { value: 12.4, deltaVs7d: 0.8 },
  accuracy: { value: 54.2, deltaVs7d: -0.3 },
  brier7d: { value: 0.189, deltaVs7d: -0.004 },
  bankroll: { value: 1240, currency: 'EUR' },
};

describe('StatStrip', () => {
  it('renders 4 stat tiles with labels and values', () => {
    render(<StatStrip data={data} />);
    expect(screen.getByText(/Résultat 30J/i)).toBeInTheDocument();
    expect(screen.getByText(/12\.4%/)).toBeInTheDocument();
    expect(screen.getByText(/Précision/i)).toBeInTheDocument();
    expect(screen.getByText(/54\.2%/)).toBeInTheDocument();
    expect(screen.getByText(/Qualité probas 7J/i)).toBeInTheDocument();
    expect(screen.getByText(/Capital suivi/i)).toBeInTheDocument();
    expect(screen.getByText(/1\s?240/)).toBeInTheDocument();
    expect(screen.queryByText(/ROI/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Accuracy/i)).not.toBeInTheDocument();
  });

  it('shows a skeleton when loading', () => {
    render(<StatStrip loading />);
    expect(screen.getAllByTestId('stat-tile-skeleton')).toHaveLength(4);
  });

  it('accepts a data-testid prop on the root', () => {
    render(<StatStrip data={data} data-testid="custom-strip" />);
    expect(screen.getByTestId('custom-strip')).toBeInTheDocument();
  });

  it('has no axe violations', async () => {
    const { container } = render(<StatStrip data={data} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
