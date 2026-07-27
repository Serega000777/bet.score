'use client';

import { useCallback, useEffect, useState } from 'react';

import {
  formatEventDate,
  getEvents,
  statusLabels,
  type SportingEvent,
} from '../lib/events';

type CatalogState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; events: SportingEvent[] };

export function EventCatalog() {
  const [state, setState] = useState<CatalogState>({ kind: 'loading' });
  const [requestKey, setRequestKey] = useState(0);

  const retry = useCallback(() => {
    setState({ kind: 'loading' });
    setRequestKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getEvents(controller.signal)
      .then((events) => setState({ kind: 'ready', events }))
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
    return <CatalogMessage mark="···" title="Загружаем матчи" />;
  }
  if (state.kind === 'error') {
    return (
      <CatalogMessage mark="!" title="Матчи временно недоступны" text={state.message} error>
        <button type="button" onClick={retry}>Повторить</button>
      </CatalogMessage>
    );
  }
  if (state.events.length === 0) {
    return (
      <CatalogMessage
        mark="○"
        title="Ближайших матчей нет"
        text="Новые события появятся после обновления источника данных."
      />
    );
  }

  return (
    <div className="match-list">
      {state.events.map((event) => (
        <article className="match-card" key={event.id}>
          <div className="match-meta">
            <span>{event.competition}</span>
            <time dateTime={event.starts_at}>{formatEventDate(event.starts_at)}</time>
          </div>
          <div className="match-teams">
            <Team participant={event.home} />
            <span className="match-score">{score(event)}</span>
            <Team participant={event.away} away />
          </div>
          <span className={`match-status status-${event.status}`}>
            {statusLabels[event.status]}
          </span>
        </article>
      ))}
    </div>
  );
}

function Team({
  participant,
  away = false,
}: {
  participant: SportingEvent['home'];
  away?: boolean;
}) {
  return (
    <div className={`match-team${away ? ' away' : ''}`}>
      <i>{participant.short_name}</i>
      <strong>{participant.name}</strong>
    </div>
  );
}

function score(event: SportingEvent): string {
  if (event.home.score === null || event.away.score === null) {
    return 'VS';
  }
  return `${event.home.score}:${event.away.score}`;
}

function CatalogMessage({
  mark,
  title,
  text,
  error = false,
  children,
}: {
  mark: string;
  title: string;
  text?: string;
  error?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className={`catalog-message${error ? ' error' : ''}`} role={error ? 'alert' : 'status'}>
      <i>{mark}</i>
      <strong>{title}</strong>
      {text && <span>{text}</span>}
      {children}
    </div>
  );
}
