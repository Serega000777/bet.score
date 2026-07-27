import type { EventList, SportingEvent } from '@bet-score/contracts';

export {
  statusLabels,
  type SportingEvent,
} from '@bet-score/contracts';

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

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

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
