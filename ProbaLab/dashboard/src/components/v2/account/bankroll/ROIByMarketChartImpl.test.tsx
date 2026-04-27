import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ROIByMarketChartImpl } from './ROIByMarketChartImpl';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Bar: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Cell: () => <span data-testid="cell" />,
  ReferenceLine: () => <span data-testid="reference-line" />,
  XAxis: () => <span data-testid="x-axis" />,
  YAxis: () => <span data-testid="y-axis" />,
  Tooltip: ({ formatter }: { formatter: (value: number) => [string, string] }) => {
    const [, label] = formatter(12.3);
    return <span data-testid="tooltip-label">{label}</span>;
  },
}));

describe('ROIByMarketChartImpl', () => {
  it('uses performance wording in the chart tooltip', () => {
    render(
      <ROIByMarketChartImpl
        data={[
          { market: '1X2', roi_pct: 12.3, n: 10, wins: 6, losses: 4, voids: 0 },
        ]}
      />,
    );

    expect(screen.getByTestId('tooltip-label')).toHaveTextContent('Performance');
    expect(screen.queryByText(/ROI/i)).not.toBeInTheDocument();
  });
});
