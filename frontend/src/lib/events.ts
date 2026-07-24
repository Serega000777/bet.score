export type EventStatus = 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled';

export type Participant = {
  id: string;
  name: string;
  short_name: string;
  role: 'home' | 'away';
  score: number | null;
};

export type SportingEvent = {
  id: string;
  sport: string;
  competition_id: string;
  competition: string;
  country_code: string | null;
  starts_at: string;
  status: EventStatus;
  home: Participant;
  away: Participant;
};

export type EventList = {
  items: SportingEvent[];
  count: number;
};

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

export const statusLabels: Record<EventStatus, string> = {
  scheduled: 'Скоро',
  live: 'LIVE',
  finished: 'Завершён',
  postponed: 'Перенесён',
  cancelled: 'Отменён',
};

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
