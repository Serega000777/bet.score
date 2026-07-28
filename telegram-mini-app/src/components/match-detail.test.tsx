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
    let eventRequests = 0;
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes('/saved-events/')) return response({ saved: false });
      if (url.endsWith('/provenance')) return response({ items: [], count: 0 });
      eventRequests += 1;
      return eventRequests === 1 ? response({}, 503) : response(event);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<MatchDetail eventId={event.id} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить' }));

    expect(await screen.findByText('1:0')).toBeDefined();
    expect(eventRequests).toBe(2);
  });

  it('обновляет канонические факты после LIVE-сигнала', async () => {
    let eventRequests = 0;
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes('/saved-events/')) return response({ saved: false });
      if (url.endsWith('/provenance')) return response({ items: [], count: 0 });
      eventRequests += 1;
      return eventRequests === 1
        ? response(event)
        : response({
          ...event,
          home: { ...event.home, score: 2 },
          away: { ...event.away, score: 1 },
        });
    });
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('WebSocket', FakeWebSocket);

    render(<MatchDetail eventId={event.id} />);
    expect(await screen.findByText('1:0')).toBeDefined();
    await waitFor(() => expect(eventRequests).toBe(1));

    FakeWebSocket.instance?.emit(
      'message',
      new MessageEvent('message', {
        data: JSON.stringify({
          type: 'event.updated',
          protocol_version: 1,
          event_id: event.id,
        }),
      }),
    );

    expect(await screen.findByText('2:1')).toBeDefined();
    expect(eventRequests).toBe(2);
  });

  it('идемпотентно сохраняет и удаляет матч', async () => {
    const fetchMock = vi.fn<
      (input: string | URL | Request, init?: RequestInit) => Promise<Response>
    >(async (input) =>
      String(input).endsWith('/provenance')
        ? response({ items: [], count: 0 })
        : response(event),
    );
    vi.stubGlobal('fetch', fetchMock);

    render(<MatchDetail eventId={event.id} />);
    const button = await screen.findByRole('button', { name: 'Сохранить матч' });
    fireEvent.click(button);
    expect(await screen.findByRole('button', { name: 'Сохранено ✓' })).toBeDefined();
    fireEvent.click(screen.getByRole('button', { name: 'Сохранено ✓' }));
    expect(await screen.findByRole('button', { name: 'Сохранить матч' })).toBeDefined();

    const mutations = fetchMock.mock.calls.filter((call) =>
      String(call[0]).includes('/saved-events/') && call[1]?.method,
    );
    expect(mutations[0]?.[1]).toMatchObject({ method: 'PUT' });
    expect(mutations[1]?.[1]).toMatchObject({ method: 'DELETE' });
  });

  it('восстанавливает сохранённое состояние с сервера', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string | URL | Request) => {
        const url = String(input);
        if (url.includes('/saved-events/')) return response({ saved: true });
        if (url.endsWith('/provenance')) return response({ items: [], count: 0 });
        return response(event);
      }),
    );

    render(<MatchDetail eventId={event.id} />);

    expect(await screen.findByRole('button', { name: 'Сохранено ✓' })).toBeDefined();
  });
});

class FakeWebSocket {
  static instance: FakeWebSocket | null = null;
  private readonly listeners = new Map<string, EventListener>();

  constructor(readonly url: string) {
    FakeWebSocket.instance = this;
  }

  addEventListener(type: string, listener: EventListener): void {
    this.listeners.set(type, listener);
  }

  emit(type: string, event: Event): void {
    this.listeners.get(type)?.(event);
  }

  close(): void {
    return undefined;
  }
}

function response(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
