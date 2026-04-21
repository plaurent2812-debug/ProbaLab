import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'jest-axe';
import { BottomNavV2 } from './BottomNavV2';

describe('BottomNavV2', () => {
  it('renders 3 nav items', () => {
    render(
      <MemoryRouter>
        <BottomNavV2 />
      </MemoryRouter>
    );
    expect(screen.getByRole('link', { name: /accueil/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /matchs/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /compte/i })).toBeInTheDocument();
  });

  it('is labeled as navigation landmark', () => {
    render(
      <MemoryRouter>
        <BottomNavV2 />
      </MemoryRouter>
    );
    expect(screen.getByRole('navigation', { name: /navigation mobile/i })).toBeInTheDocument();
  });

  it('is hidden on desktop (>= md) via responsive classes', () => {
    render(
      <MemoryRouter>
        <BottomNavV2 />
      </MemoryRouter>
    );
    const nav = screen.getByRole('navigation', { name: /navigation mobile/i });
    expect(nav.className).toMatch(/flex/);
    expect(nav.className).toMatch(/md:hidden/);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <BottomNavV2 />
      </MemoryRouter>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
