'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import {
  formatEventDate,
  getEvents,
  statusLabels,
  type SportingEvent,
} from '@/lib/events';

type State =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; events: SportingEvent[] };

export function EventCatalog() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [requestKey, setRequestKey] = useState(0);

  const retry = useCallback(() => {
    setState({ kind: 'loading' });
    setRequestKey((key) => key + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getEvents(controller.signal)
      .then((payload) => setState({ kind: 'ready', events: payload.items }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setState({
            kind: 'error',
            message: error instanceof Error ? error.message : 'Неизвестная ошибка',
          });
        }
      });
    return () => controller.abort();
  }, [requestKey]);

  if (state.kind === 'loading') {
    return (
      <div className="catalog-state" aria-live="polite">
        <div className="spinner" />
        <strong>Загружаем матчи</strong>
        <span>Получаем актуальный каталог событий</span>
      </div>
    );
  }

  if (state.kind === 'error') {
    return (
      <div className="catalog-state error-state" role="alert">
        <span className="state-mark">!</span>
        <strong>Каталог временно недоступен</strong>
        <span>{state.message}</span>
        <button type="button" onClick={retry}>Повторить</button>
      </div>
    );
  }

  if (state.events.length === 0) {
    return (
      <div className="catalog-state">
        <span className="state-mark">○</span>
        <strong>Ближайших матчей нет</strong>
        <span>Новые события появятся после обновления источника данных.</span>
      </div>
    );
  }

  return (
    <div className="event-list">
      {state.events.map((event) => (
        <Link className="event-card" href={`/matches/${event.id}`} key={event.id}>
          <div className="event-meta">
            <span>{event.sport} · {event.competition}</span>
            <time dateTime={event.starts_at}>{formatEventDate(event.starts_at)}</time>
          </div>
          <div className="event-teams">
            <div><i>{event.home.short_name}</i><strong>{event.home.name}</strong></div>
            <span className="versus">VS</span>
            <div className="away"><i>{event.away.short_name}</i><strong>{event.away.name}</strong></div>
          </div>
          <div className="event-footer">
            <span className={`status status-${event.status}`}>{statusLabels[event.status]}</span>
            <span>Открыть аналитику →</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
