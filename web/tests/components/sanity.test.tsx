import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

function Greeting({ name }: { name: string }) {
  return <p>Hello, {name}!</p>;
}

describe('Test setup sanity', () => {
  it('renders a component and finds text', () => {
    render(<Greeting name="ProbaLab" />);
    expect(screen.getByText('Hello, ProbaLab!')).toBeInTheDocument();
  });
});
