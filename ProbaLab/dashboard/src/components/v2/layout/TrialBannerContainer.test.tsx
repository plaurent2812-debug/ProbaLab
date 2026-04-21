import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrialBannerContainer } from './TrialBannerContainer';

describe('TrialBannerContainer', () => {
  it('renders the banner when role is trial and daysLeft is defined', () => {
    render(<TrialBannerContainer userRole="trial" trialDaysLeft={12} trialEndDate="2026-05-21" />);
    expect(screen.getByRole('region', { name: /trial/i })).toBeInTheDocument();
    expect(screen.getByText(/j-12/i)).toBeInTheDocument();
  });

  it('renders nothing when role is not trial', () => {
    const { container } = render(<TrialBannerContainer userRole="free" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when daysLeft is missing on trial', () => {
    const { container } = render(<TrialBannerContainer userRole="trial" />);
    expect(container).toBeEmptyDOMElement();
  });
});
