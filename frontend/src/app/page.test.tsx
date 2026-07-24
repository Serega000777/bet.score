import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import HomePage from './page';

describe('HomePage', () => {
  it('объясняет аналитическое назначение продукта', () => {
    render(<HomePage />);
    expect(screen.getByText(/не призывает делать ставки/i)).toBeDefined();
  });
});
