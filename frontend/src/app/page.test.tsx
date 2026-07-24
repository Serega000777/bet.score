import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import HomePage from './page';

describe('HomePage', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => {})),
    );
  });

  it('объясняет аналитическое назначение продукта', () => {
    render(<HomePage />);
    expect(screen.getByText(/не призывает делать ставки/i)).toBeDefined();
  });
});
