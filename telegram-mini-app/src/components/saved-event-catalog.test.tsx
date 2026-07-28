import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { SavedEventCatalog } from './saved-event-catalog';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it('показывает сохранённые матчи пользователя', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      new Response(
        JSON.stringify({
          count: 1,
          items: [{
            id: '70000000-0000-0000-0000-000000000001',
            sport_code: 'football',
            sport: 'Футбол',
            competition_id: '70000000-0000-0000-0000-000000000002',
            competition: 'Премьер-лига',
            country_code: 'RU',
            starts_at: '2026-08-01T17:00:00Z',
            status: 'scheduled',
            home: { id: '1', name: 'Север', short_name: 'SEV', role: 'home', score: null },
            away: { id: '2', name: 'Восток', short_name: 'VOS', role: 'away', score: null },
          }],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    ),
  );

  render(<SavedEventCatalog />);

  expect(await screen.findByText('Север — Восток')).toBeDefined();
  expect(screen.getByRole('link').getAttribute('href')).toBe(
    '/matches/70000000-0000-0000-0000-000000000001',
  );
});
