import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ROIChart } from './ROIChart';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  AreaChart: ({ children }: { children: ReactNode }) => <svg>{children}</svg>,
  Area: () => <g data-testid="area" />,
  CartesianGrid: () => <g data-testid="grid" />,
  XAxis: () => <g data-testid="x-axis" />,
  YAxis: () => <g data-testid="y-axis" />,
  Tooltip: ({ formatter }: { formatter: (value: number) => [string, string] }) => {
    const [, label] = formatter(12.34);
    return <text data-testid="tooltip-label">{label}</text>;
  },
}));

describe('ROIChart', () => {
  it('uses cumulative result wording in the chart tooltip', () => {
    render(<ROIChart data={[{ date: '2026-04-27', roi: 12.34 }]} />);

    expect(screen.getByTestId('tooltip-label')).toHaveTextContent('Résultat cumulé');
    expect(screen.queryByText(/ROI/i)).not.toBeInTheDocument();
  });
});
