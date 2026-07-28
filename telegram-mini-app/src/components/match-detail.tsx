'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import {
  EventRequestError,
  formatEventDate,
  getEvent,
  getEventProvenance,
  removeSavedEvent,
  saveEvent,
  subscribeToEvent,
  statusLabels,
  type EventProvenance,
  type SportingEvent,
} from '../lib/events';

type DetailState =
  | { kind: 'loading' }
  | { kind: 'not-found' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; event: SportingEvent };

export function MatchDetail({ eventId }: { eventId: string }) {
  const [state, setState] = useState<DetailState>({ kind: 'loading' });
  const [requestKey, setRequestKey] = useState(0);
  const retry = useCallback(() => {
    setState({ kind: 'loading' });
    setRequestKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getEvent(eventId, controller.signal)
      .then((event) => setState({ kind: 'ready', event }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof EventRequestError && error.status === 404) {
          setState({ kind: 'not-found' });
          return;
        }
        setState({
          kind: 'error',
          message: error instanceof Error ? error.message : 'Неизвестная ошибка',
        });
      });
    return () => controller.abort();
  }, [eventId, requestKey]);

  useEffect(() => {
    if (state.kind !== 'ready') return;
    return subscribeToEvent(eventId, () => {
      getEvent(eventId)
        .then((event) => setState({ kind: 'ready', event }))
        .catch(() => undefined);
    });
  }, [eventId, state.kind]);

  if (state.kind === 'loading') {
    return <DetailMessage title="Загружаем матч" mark="···" />;
  }
  if (state.kind === 'not-found') {
    return <DetailMessage title="Матч не найден" text="Возможно, событие было удалено." mark="○" />;
  }
  if (state.kind === 'error') {
    return (
      <DetailMessage title="Матч временно недоступен" text={state.message} mark="!" error>
        <button type="button" onClick={retry}>Повторить</button>
      </DetailMessage>
    );
  }

  const { event } = state;
  return (
    <section className="match-detail">
      <div className="detail-meta">
        <span>{event.sport} · {event.competition}</span>
        <span className={`match-status status-${event.status}`}>{statusLabels[event.status]}</span>
      </div>
      <time dateTime={event.starts_at}>{formatEventDate(event.starts_at)}</time>
      <div className="detail-teams">
        <DetailTeam name={event.home.name} shortName={event.home.short_name} />
        <strong>{score(event)}</strong>
        <DetailTeam name={event.away.name} shortName={event.away.short_name} away />
      </div>
      <SaveEventButton eventId={event.id} />
      <section className="analysis-pending">
        <p className="eyebrow">ОБЪЯСНИМЫЙ АНАЛИЗ</p>
        <h2>Факты собираются</h2>
        <p>
          Анализ появится только после проверки источников и сохранения provenance.
          bet.score не подменяет отсутствующие данные догадками.
        </p>
      </section>
      <Provenance eventId={event.id} />
    </section>
  );
}

function SaveEventButton({ eventId }: { eventId: string }) {
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  const toggle = async () => {
    setPending(true);
    setFailed(false);
    try {
      if (saved) {
        await removeSavedEvent(eventId);
      } else {
        await saveEvent(eventId);
      }
      setSaved((value) => !value);
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="save-event">
      <button type="button" disabled={pending} aria-pressed={saved} onClick={toggle}>
        {pending ? 'Сохраняем…' : saved ? 'Сохранено ✓' : 'Сохранить матч'}
      </button>
      {failed && <span role="alert">Не удалось изменить сохранённые матчи.</span>}
    </div>
  );
}

function Provenance({ eventId }: { eventId: string }) {
  const [sources, setSources] = useState<EventProvenance[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getEventProvenance(eventId, controller.signal)
      .then(setSources)
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [eventId]);

  return (
    <section className="provenance">
      <p className="eyebrow">ИСТОЧНИКИ ДАННЫХ</p>
      {sources === null && !failed && <p role="status">Проверяем происхождение фактов…</p>}
      {failed && <p role="alert">Источники временно недоступны.</p>}
      {sources?.length === 0 && <p>Для этого события источник пока не зафиксирован.</p>}
      {sources && sources.length > 0 && (
        <ul>
          {sources.map((source) => (
            <li key={`${source.provider_key}:${source.version}`}>
              <strong>{source.provider_key}</strong>
              <span>Версия {source.version}</span>
              <time dateTime={source.observed_at}>
                Наблюдение: {formatEventDate(source.observed_at)}
              </time>
              <code title={source.checksum}>{source.checksum.slice(0, 12)}…</code>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function DetailTeam({
  name,
  shortName,
  away = false,
}: {
  name: string;
  shortName: string;
  away?: boolean;
}) {
  return (
    <div className={`detail-team${away ? ' away' : ''}`}>
      <i>{shortName}</i>
      <strong>{name}</strong>
    </div>
  );
}

function score(event: SportingEvent): string {
  return event.home.score === null || event.away.score === null
    ? 'VS'
    : `${event.home.score}:${event.away.score}`;
}

function DetailMessage({
  title,
  mark,
  text,
  error = false,
  children,
}: {
  title: string;
  mark: string;
  text?: string;
  error?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <section className={`state-card detail-state${error ? ' error' : ''}`} role={error ? 'alert' : 'status'}>
      <i>{mark}</i>
      <h1>{title}</h1>
      {text && <p>{text}</p>}
      {children}
      <Link className="back-link" href="/">← К каталогу</Link>
    </section>
  );
}
