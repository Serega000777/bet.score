'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import {
  formatEventDate,
  getSavedEvents,
  statusLabels,
  type SportingEvent,
} from '../lib/events';

type State =
  | { kind: 'loading' }
  | { kind: 'error' }
  | { kind: 'ready'; events: SportingEvent[] };

export function SavedEventCatalog() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    getSavedEvents(controller.signal)
      .then((events) => setState({ kind: 'ready', events }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: 'error' });
      });
    return () => controller.abort();
  }, []);

  if (state.kind === 'loading') return <p role="status">Загружаем сохранённые матчи…</p>;
  if (state.kind === 'error') return <p role="alert">Сохранённые матчи временно недоступны.</p>;
  if (state.events.length === 0) {
    return <p role="status">Вы ещё не сохранили ни одного матча.</p>;
  }

  return (
    <div className="saved-match-list">
      {state.events.map((event) => (
        <Link className="saved-match-card" href={`/matches/${event.id}`} key={event.id}>
          <span>{event.competition}</span>
          <strong>{event.home.name} — {event.away.name}</strong>
          <time dateTime={event.starts_at}>{formatEventDate(event.starts_at)}</time>
          <small>{statusLabels[event.status]}</small>
        </Link>
      ))}
    </div>
  );
}
