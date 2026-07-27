import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import MiniAppPage from './page';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it('после действующей сессии показывает пользователя и каталог', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(
      jsonResponse({
        id: '50000000-0000-0000-0000-000000000001',
        display_name: 'Иван Петров',
        username: 'ivan',
        locale: 'ru',
      }),
    )
    .mockResolvedValueOnce(
      jsonResponse({
        count: 1,
        items: [
          {
            id: '70000000-0000-0000-0000-000000000001',
            sport: 'Футбол',
            competition_id: '70000000-0000-0000-0000-000000000002',
            competition: 'Премьер-лига',
            country_code: 'RU',
            starts_at: '2026-08-01T17:00:00Z',
            status: 'scheduled',
            home: { id: '1', name: 'Север', short_name: 'SEV', role: 'home', score: null },
            away: { id: '2', name: 'Восток', short_name: 'VOS', role: 'away', score: null },
          },
        ],
      }),
    );
  vi.stubGlobal('fetch', fetchMock);

  render(<MiniAppPage />);

  expect(await screen.findByRole('heading', { name: /Иван Петров/ })).toBeDefined();
  expect(await screen.findByText('Премьер-лига')).toBeDefined();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
