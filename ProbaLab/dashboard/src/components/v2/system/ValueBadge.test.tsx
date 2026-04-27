import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { ValueBadge } from './ValueBadge';

describe('ValueBadge', () => {
  it('formats edge as percentage with one decimal', () => {
    render(<ValueBadge edge={0.072} />);
    expect(screen.getByText(/\+7\.2%/)).toBeInTheDocument();
  });

  it('uses aria-label with SIGNAL wording', () => {
    render(<ValueBadge edge={0.072} />);
    expect(screen.getByLabelText(/signal modèle \+7\.2%/i)).toBeInTheDocument();
    expect(screen.getByText(/SIGNAL/i)).toBeInTheDocument();
  });

  it('rounds to one decimal', () => {
    render(<ValueBadge edge={0.05678} />);
    expect(screen.getByText(/\+5\.7%/)).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<ValueBadge edge={0.072} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
