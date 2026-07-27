import type { EventList, SportingEvent } from '@bet-score/contracts';

export {
  statusLabels,
  type EventStatus,
  type Participant,
  type SportingEvent,
} from '@bet-score/contracts';

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) {
    let message = 'Не удалось загрузить данные';
    try {
      const payload = (await response.json()) as { message?: string };
      message = payload.message ?? message;
    } catch {
      // Ответ внешнего контура может не содержать JSON.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export function getEvents(signal?: AbortSignal): Promise<EventList> {
  return request<EventList>('/events', signal);
}

export function getEvent(id: string, signal?: AbortSignal): Promise<SportingEvent> {
  return request<SportingEvent>(`/events/${encodeURIComponent(id)}`, signal);
}

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
