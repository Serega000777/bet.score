'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import {
  formatEventDate,
  getCompetitions,
  getEvents,
  getSports,
  statusLabels,
  type CompetitionSummary,
  type SportingEvent,
  type SportSummary,
} from '../lib/events';

type CatalogState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; events: SportingEvent[] };

export function EventCatalog() {
  const [state, setState] = useState<CatalogState>({ kind: 'loading' });
  const [sports, setSports] = useState<SportSummary[] | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [sportCode, setSportCode] = useState('');
  const [competitionId, setCompetitionId] = useState('');
  const [requestKey, setRequestKey] = useState(0);

  const retry = useCallback(() => {
    setState({ kind: 'loading' });
    setRequestKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getSports(controller.signal), getCompetitions(controller.signal)])
      .then(([sportItems, competitionItems]) => {
        setSports(sportItems);
        setCompetitions(competitionItems);
      })
      .catch(() => {
        if (!controller.signal.aborted) setSports([]);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getEvents(
      {
        sport_code: sportCode || undefined,
        competition_id: competitionId || undefined,
      },
      controller.signal,
    )
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
  }, [competitionId, requestKey, sportCode]);

  if (state.kind === 'loading' && sports === null) {
    return <CatalogMessage mark="···" title="Загружаем матчи" />;
  }
  if (state.kind === 'error') {
    return (
      <CatalogMessage
        mark="!"
        title="Матчи временно недоступны"
        text={state.message}
        error
      >
        <button type="button" onClick={retry}>Повторить</button>
      </CatalogMessage>
    );
  }

  const visibleCompetitions = competitions.filter(
    (item) => sportCode === '' || item.sport_code === sportCode,
  );

  return (
    <>
      {sports && sports.length > 0 && (
        <nav className="catalog-filters" aria-label="Фильтры матчей">
          <div className="sport-filter">
            <FilterButton
              active={sportCode === ''}
              label="Все"
              onClick={() => {
                setSportCode('');
                setCompetitionId('');
              }}
            />
            {sports.map((item) => (
              <FilterButton
                active={sportCode === item.code}
                count={item.event_count}
                key={item.code}
                label={item.name}
                onClick={() => {
                  setSportCode(item.code);
                  setCompetitionId('');
                }}
              />
            ))}
          </div>
          <label>
            <span>Соревнование</span>
            <select
              value={competitionId}
              onChange={(event) => setCompetitionId(event.target.value)}
            >
              <option value="">Все соревнования</option>
              {visibleCompetitions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.event_count})
                </option>
              ))}
            </select>
          </label>
        </nav>
      )}
      {state.kind === 'loading' && <CatalogMessage mark="···" title="Обновляем матчи" />}
      {state.kind === 'ready' && state.events.length === 0 && (
        <CatalogMessage
          mark="○"
          title="По выбранным фильтрам матчей нет"
          text="Выберите другой вид спорта или соревнование."
        />
      )}
      {state.kind === 'ready' && state.events.length > 0 && (
        <div className="match-list">
          {state.events.map((event) => (
            <Link
              aria-label={`${event.home.name} — ${event.away.name}`}
              className="match-card"
              href={`/matches/${event.id}`}
              key={event.id}
            >
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
              <span className="open-match">Открыть →</span>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}

function FilterButton({
  active,
  label,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  count?: number;
  onClick: () => void;
}) {
  return (
    <button aria-pressed={active} type="button" onClick={onClick}>
      {label} {count !== undefined && <small>{count}</small>}
    </button>
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
  if (event.home.score === null || event.away.score === null) return 'VS';
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
