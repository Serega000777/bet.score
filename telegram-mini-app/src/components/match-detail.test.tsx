import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { MatchDetail } from './match-detail';

const event = {
  id: '70000000-0000-0000-0000-000000000001',
  sport: 'Футбол',
  competition_id: '70000000-0000-0000-0000-000000000002',
  competition: 'Премьер-лига',
  country_code: 'RU',
  starts_at: '2026-08-01T17:00:00Z',
  status: 'live',
  home: { id: '1', name: 'Север', short_name: 'SEV', role: 'home', score: 1 },
  away: { id: '2', name: 'Восток', short_name: 'VOS', role: 'away', score: 0 },
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('MatchDetail', () => {
  it('показывает только подтверждённые факты матча', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string | URL | Request) =>
        String(input).endsWith('/provenance')
          ? response({
              count: 1,
              items: [
                {
                  provider_key: 'test-provider',
                  version: 'v2',
                  observed_at: '2026-08-01T16:59:00Z',
                  ingested_at: '2026-08-01T16:59:05Z',
                  checksum: 'a'.repeat(64),
                },
              ],
            })
          : response(event),
      ),
    );

    render(<MatchDetail eventId={event.id} />);

    expect(await screen.findByText('1:0')).toBeDefined();
    expect(screen.getByText(/Премьер-лига/)).toBeDefined();
    expect(screen.getByText(/не подменяет отсутствующие данные догадками/i)).toBeDefined();
    expect(await screen.findByText('test-provider')).toBeDefined();
    expect(screen.getByText('Версия v2')).toBeDefined();
  });

  it('отличает отсутствующий матч от временной ошибки', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({}, 404)));

    render(<MatchDetail eventId="missing" />);

    expect(await screen.findByText('Матч не найден')).toBeDefined();
    expect(screen.queryByRole('button', { name: 'Повторить' })).toBeNull();
  });

  it('повторяет временно неуспешный запрос', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response({}, 503))
      .mockResolvedValueOnce(response(event))
      .mockResolvedValueOnce(response({ items: [], count: 0 }));
    vi.stubGlobal('fetch', fetchMock);

    render(<MatchDetail eventId={event.id} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText('1:0')).toBeDefined();
  });
});

function response(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
