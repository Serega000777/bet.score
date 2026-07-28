'use client';

import { useEffect, useState } from 'react';

import { EventCatalog } from '../components/event-catalog';
import { SavedEventCatalog } from '../components/saved-event-catalog';

type User = {
  id: string;
  display_name: string;
  username: string | null;
  locale: string;
};

type State =
  | { kind: 'loading' }
  | { kind: 'browser' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; user: User };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

async function requestUser(path: string, init?: RequestInit): Promise<User> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as {
      message?: string;
      detail?: string;
    };
    throw new Error(payload.message ?? payload.detail ?? 'Ошибка авторизации');
  }
  return (await response.json()) as User;
}

export default function MiniAppPage() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    const authenticate = async () => {
      try {
        const existingUser = await requestUser('/auth/me');
        setState({ kind: 'ready', user: existingUser });
        return;
      } catch {
        // Отсутствующая сессия ожидаема при первом запуске Mini App.
      }

      const webApp = window.Telegram?.WebApp;
      if (!webApp?.initData) {
        setState({ kind: 'browser' });
        return;
      }

      webApp.ready();
      webApp.expand();
      try {
        const user = await requestUser('/auth/telegram', {
          method: 'POST',
          body: JSON.stringify({ init_data: webApp.initData }),
        });
        webApp.HapticFeedback?.notificationOccurred('success');
        setState({ kind: 'ready', user });
      } catch (error) {
        webApp.HapticFeedback?.notificationOccurred('error');
        setState({
          kind: 'error',
          message: error instanceof Error ? error.message : 'Неизвестная ошибка',
        });
      }
    };

    void authenticate();
  }, []);

  return (
    <main>
      <header><strong>bet.score</strong><span>MINI APP</span></header>
      {state.kind === 'loading' && <StateCard mark="···" title="Проверяем сессию" text="Безопасно связываемся с Telegram" />}
      {state.kind === 'browser' && <StateCard mark="↗" title="Откройте приложение в Telegram" text="Авторизация доступна только при запуске через официальную кнопку Mini App." />}
      {state.kind === 'error' && <StateCard mark="!" title="Не удалось войти" text={state.message} error />}
      {state.kind === 'ready' && <Dashboard user={state.user} />}
      <footer>Аналитика, а не призыв к ставкам.</footer>
    </main>
  );
}

function StateCard({ mark, title, text, error = false }: { mark: string; title: string; text: string; error?: boolean }) {
  return <section className={`state-card${error ? ' error' : ''}`}><i>{mark}</i><h1>{title}</h1><p>{text}</p></section>;
}

function Dashboard({ user }: { user: User }) {
  const [section, setSection] = useState<'catalog' | 'saved'>('catalog');

  return (
    <section className="dashboard">
      <p className="eyebrow">СЕССИЯ ПОДТВЕРЖДЕНА</p>
      <h1>Здравствуйте,<br />{user.display_name}</h1>
      <p>Telegram-профиль безопасно связан с bet.score. Ниже доступен общий каталог актуальных спортивных событий.</p>
      <div className="identity-card"><span>Аккаунт</span><strong>{user.username ? `@${user.username}` : 'Telegram'}</strong><span>Язык</span><strong>{user.locale.toUpperCase()}</strong></div>
      <nav className="dashboard-tabs" aria-label="Разделы матчей">
        <button type="button" aria-pressed={section === 'catalog'} onClick={() => setSection('catalog')}>Все матчи</button>
        <button type="button" aria-pressed={section === 'saved'} onClick={() => setSection('saved')}>Сохранённые</button>
      </nav>
      <section className="matches">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{section === 'catalog' ? 'БЛИЖАЙШИЕ СОБЫТИЯ' : 'ВАША ПОДБОРКА'}</p>
            <h2>{section === 'catalog' ? 'Матчи' : 'Сохранённые матчи'}</h2>
          </div>
          <span>Ваше время</span>
        </div>
        {section === 'catalog' ? <EventCatalog /> : <SavedEventCatalog />}
      </section>
    </section>
  );
}
