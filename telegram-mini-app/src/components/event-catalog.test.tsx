import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EventCatalog } from './event-catalog';

const event = {
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

const sports = [{ code: 'football', name: 'Футбол', event_count: 1 }];
const competitions = [
  {
    id: event.competition_id,
    sport_code: 'football',
    name: event.competition,
    country_code: 'RU',
    event_count: 1,
  },
];

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('EventCatalog', () => {
  it('показывает полученные матчи и навигацию', async () => {
    vi.stubGlobal('fetch', vi.fn((input: string | URL | Request) => catalogResponse(input, [event])));

    render(<EventCatalog />);

    expect(await screen.findByText('Премьер-лига')).toBeDefined();
    expect(screen.getByRole('button', { name: /Футбол 1/ })).toBeDefined();
    expect(screen.getByRole('combobox', { name: 'Соревнование' })).toBeDefined();
    expect(screen.getByText('Север')).toBeDefined();
    expect(screen.getByText('Восток')).toBeDefined();
    expect(
      screen.getByRole('link', { name: 'Север — Восток' }).getAttribute('href'),
    ).toBe(`/matches/${event.id}`);
  });

  it('передаёт выбранный вид спорта в API событий', async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => catalogResponse(input, [event]));
    vi.stubGlobal('fetch', fetchMock);
    render(<EventCatalog />);

    fireEvent.click(await screen.findByRole('button', { name: /Футбол 1/ }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([input]) =>
          String(input).includes('/events?sport_code=football'),
        ),
      ).toBe(true),
    );
  });

  it('показывает пустое состояние для выбранных фильтров', async () => {
    vi.stubGlobal('fetch', vi.fn((input: string | URL | Request) => catalogResponse(input, [])));

    render(<EventCatalog />);

    expect(await screen.findByText('По выбранным фильтрам матчей нет')).toBeDefined();
  });

  it('позволяет повторить запрос после ошибки', async () => {
    let eventRequests = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn((input: string | URL | Request) => {
        const url = String(input);
        if (url.includes('/events')) {
          eventRequests += 1;
          return eventRequests === 1
            ? jsonResponse({}, 503)
            : jsonResponse({ items: [event], count: 1 });
        }
        return catalogResponse(input, [event]);
      }),
    );

    render(<EventCatalog />);
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить' }));

    expect(await screen.findByText('Премьер-лига')).toBeDefined();
    expect(eventRequests).toBe(2);
  });
});

function catalogResponse(
  input: string | URL | Request,
  events: unknown[],
): Promise<Response> {
  const url = String(input);
  if (url.endsWith('/sports')) return Promise.resolve(jsonResponse({ items: sports, count: 1 }));
  if (url.endsWith('/competitions')) {
    return Promise.resolve(jsonResponse({ items: competitions, count: 1 }));
  }
  return Promise.resolve(jsonResponse({ items: events, count: events.length }));
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
