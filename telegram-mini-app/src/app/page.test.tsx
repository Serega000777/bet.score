import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import MiniAppPage from './page';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it('после действующей сессии показывает пользователя и каталог', async () => {
  const match = {
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
  };
  let requestNumber = 0;
  const fetchMock = vi.fn((input: string | URL | Request) => {
    requestNumber += 1;
    const url = String(input);
    if (requestNumber === 1) {
      return Promise.resolve(jsonResponse({
        id: '50000000-0000-0000-0000-000000000001',
        display_name: 'Иван Петров',
        username: 'ivan',
        locale: 'ru',
      }));
    }
    if (url.endsWith('/sports')) {
      return Promise.resolve(jsonResponse({
        items: [{ code: 'football', name: 'Футбол', event_count: 1 }],
        count: 1,
      }));
    }
    if (url.endsWith('/competitions')) {
      return Promise.resolve(jsonResponse({
        items: [{
          id: match.competition_id,
          sport_code: 'football',
          name: match.competition,
          country_code: 'RU',
          event_count: 1,
        }],
        count: 1,
      }));
    }
    return Promise.resolve(jsonResponse({ count: 1, items: [match] }));
  });
  vi.stubGlobal('fetch', fetchMock);

  render(<MiniAppPage />);

  expect(await screen.findByRole('heading', { name: /Иван Петров/ })).toBeDefined();
  expect(await screen.findByText('Премьер-лига')).toBeDefined();
  expect(fetchMock).toHaveBeenCalledTimes(4);
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
