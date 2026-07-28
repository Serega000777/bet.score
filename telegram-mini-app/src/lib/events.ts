import type {
  CompetitionList,
  CompetitionSummary,
  EventList,
  EventProvenance,
  EventProvenanceList,
  EventUpdated,
  SportList,
  SportSummary,
  SportingEvent,
} from '@bet-score/contracts';

export {
  statusLabels,
  type CompetitionSummary,
  type EventProvenance,
  type SportSummary,
  type SportingEvent,
} from '@bet-score/contracts';

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export function subscribeToEvent(
  id: string,
  onUpdate: (update: EventUpdated) => void,
): () => void {
  if (typeof WebSocket === 'undefined') return () => undefined;
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;
  let attempt = 0;

  const connect = () => {
    if (stopped) return;
    socket = new WebSocket(eventWebSocketUrl(id));
    socket.addEventListener('open', () => {
      attempt = 0;
    });
    socket.addEventListener('message', (message) => {
      const update = parseEventUpdate(message.data, id);
      if (update !== null) onUpdate(update);
    });
    socket.addEventListener('close', () => {
      if (stopped) return;
      const delay = Math.min(1000 * 2 ** attempt, 30_000);
      attempt += 1;
      reconnectTimer = setTimeout(connect, delay);
    });
  };

  connect();
  return () => {
    stopped = true;
    if (reconnectTimer !== null) clearTimeout(reconnectTimer);
    socket?.close();
  };
}

function eventWebSocketUrl(id: string): string {
  const url = new URL(`${apiUrl}/live/events/${encodeURIComponent(id)}`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}

function parseEventUpdate(raw: unknown, eventId: string): EventUpdated | null {
  if (typeof raw !== 'string') return null;
  try {
    const value = JSON.parse(raw) as Partial<EventUpdated>;
    return value.type === 'event.updated' &&
      value.protocol_version === 1 &&
      value.event_id === eventId
      ? (value as EventUpdated)
      : null;
  } catch {
    return null;
  }
}

export type EventFilters = {
  sport_code?: string;
  competition_id?: string;
};

export async function getEvents(
  filters: EventFilters = {},
  signal?: AbortSignal,
): Promise<SportingEvent[]> {
  const query = new URLSearchParams();
  if (filters.sport_code) query.set('sport_code', filters.sport_code);
  if (filters.competition_id) query.set('competition_id', filters.competition_id);
  const suffix = query.size > 0 ? `?${query.toString()}` : '';
  const response = await fetch(`${apiUrl}/events${suffix}`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) {
    throw new Error('Не удалось загрузить матчи');
  }
  const payload = (await response.json()) as EventList;
  return payload.items;
}

export async function getSports(signal?: AbortSignal): Promise<SportSummary[]> {
  const response = await fetch(`${apiUrl}/sports`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) throw new Error('Не удалось загрузить виды спорта');
  return ((await response.json()) as SportList).items;
}

export async function getCompetitions(signal?: AbortSignal): Promise<CompetitionSummary[]> {
  const response = await fetch(`${apiUrl}/competitions`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) throw new Error('Не удалось загрузить соревнования');
  return ((await response.json()) as CompetitionList).items;
}

export async function getEvent(id: string, signal?: AbortSignal): Promise<SportingEvent> {
  const response = await fetch(`${apiUrl}/events/${encodeURIComponent(id)}`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) {
    throw new EventRequestError(
      response.status === 404 ? 'Матч не найден' : 'Не удалось загрузить матч',
      response.status,
    );
  }
  return (await response.json()) as SportingEvent;
}

export class EventRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export async function getEventProvenance(
  id: string,
  signal?: AbortSignal,
): Promise<EventProvenance[]> {
  const response = await fetch(`${apiUrl}/events/${encodeURIComponent(id)}/provenance`, {
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) {
    throw new Error('Не удалось загрузить источники');
  }
  const payload = (await response.json()) as EventProvenanceList;
  return payload.items;
}

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
