import type {
  EventList,
  EventProvenance,
  EventProvenanceList,
  EventUpdated,
  SportingEvent,
} from '@bet-score/contracts';

export {
  statusLabels,
  type EventProvenance,
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

export async function getEvents(signal?: AbortSignal): Promise<SportingEvent[]> {
  const response = await fetch(`${apiUrl}/events`, {
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
