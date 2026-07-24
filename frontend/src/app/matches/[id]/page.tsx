'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import {
  ApiError,
  formatEventDate,
  getEvent,
  statusLabels,
  type SportingEvent,
} from '@/lib/events';

type State =
  | { kind: 'loading' }
  | { kind: 'not-found' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; event: SportingEvent };

export default function MatchPage() {
  const params = useParams<{ id: string }>();
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    getEvent(params.id, controller.signal)
      .then((event) => setState({ kind: 'ready', event }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: 'not-found' });
          return;
        }
        setState({
          kind: 'error',
          message: error instanceof Error ? error.message : 'Неизвестная ошибка',
        });
      });
    return () => controller.abort();
  }, [params.id]);

  if (state.kind === 'loading') {
    return <main className="match-page"><div className="catalog-state"><div className="spinner" /><strong>Загружаем матч</strong></div></main>;
  }

  if (state.kind === 'not-found') {
    return <main className="match-page"><StatePage title="Матч не найден" text="Событие удалено или ссылка устарела." /></main>;
  }

  if (state.kind === 'error') {
    return <main className="match-page"><StatePage title="Не удалось открыть матч" text={state.message} /></main>;
  }

  const { event } = state;
  return (
    <main className="match-page">
      <nav className="topbar"><Link href="/">← Все матчи</Link><strong>bet.score</strong></nav>
      <section className="match-hero">
        <div className="event-meta">
          <span>{event.sport} · {event.competition}</span>
          <span className={`status status-${event.status}`}>{statusLabels[event.status]}</span>
        </div>
        <time dateTime={event.starts_at}>{formatEventDate(event.starts_at)}</time>
        <div className="scoreboard">
          <Team name={event.home.name} shortName={event.home.short_name} score={event.home.score} />
          <div className="score-divider">
            {event.home.score === null ? 'VS' : `${event.home.score} : ${event.away.score}`}
          </div>
          <Team name={event.away.name} shortName={event.away.short_name} score={event.away.score} />
        </div>
      </section>
      <section className="analysis-preview">
        <p className="eyebrow">АНАЛИТИЧЕСКИЙ КОНТУР</p>
        <h2>Основа матча подключена</h2>
        <p>Статистика, новости и AI-анализ появятся здесь после подключения подтверждённого поставщика данных.</p>
        <div className="data-quality"><span>Источник</span><strong>Локальный канонический каталог</strong><span>Статус данных</span><strong>Демонстрационные</strong></div>
      </section>
      <footer>Вероятностные оценки не являются гарантией результата.</footer>
    </main>
  );
}

function Team({ name, shortName }: { name: string; shortName: string; score: number | null }) {
  return <div className="score-team"><i>{shortName}</i><strong>{name}</strong></div>;
}

function StatePage({ title, text }: { title: string; text: string }) {
  return <div className="catalog-state"><span className="state-mark">!</span><strong>{title}</strong><span>{text}</span><Link href="/">Вернуться к матчам</Link></div>;
}
