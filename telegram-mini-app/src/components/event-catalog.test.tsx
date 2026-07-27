import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EventCatalog } from './event-catalog';

const event = {
  id: '70000000-0000-0000-0000-000000000001',
  sport: 'Футбол',
  competition_id: '70000000-0000-0000-0000-000000000002',
  competition: 'Премьер-лига',
  country_code: 'RU',
  starts_at: '2026-08-01T17:00:00Z',
  status: 'scheduled',
  home: {
    id: '1',
    name: 'Север',
    short_name: 'SEV',
    role: 'home',
    score: null,
  },
  away: {
    id: '2',
    name: 'Восток',
    short_name: 'VOS',
    role: 'away',
    score: null,
  },
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('EventCatalog', () => {
  it('показывает полученные матчи', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ items: [event], count: 1 })));

    render(<EventCatalog />);

    expect(await screen.findByText('Премьер-лига')).toBeDefined();
    expect(screen.getByText('Север')).toBeDefined();
    expect(screen.getByText('Восток')).toBeDefined();
    expect(
      screen.getByRole('link', { name: 'Север — Восток' }).getAttribute('href'),
    ).toBe(`/matches/${event.id}`);
  });

  it('показывает пустое состояние', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ items: [], count: 0 })));

    render(<EventCatalog />);

    expect(await screen.findByText('Ближайших матчей нет')).toBeDefined();
  });

  it('позволяет повторить запрос после ошибки', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({}, 503))
      .mockResolvedValueOnce(jsonResponse({ items: [event], count: 1 }));
    vi.stubGlobal('fetch', fetchMock);

    render(<EventCatalog />);
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Премьер-лига')).toBeDefined();
  });
});

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
