import { EventCatalog } from '@/components/event-catalog';

export default function HomePage() {
  return (
    <main>
      <nav className="topbar">
        <strong>bet.score</strong>
        <span className="product-status"><i /> Аналитическая платформа</span>
      </nav>

      <section className="hero compact-hero">
        <p className="eyebrow">AI SPORTS INTELLIGENCE</p>
        <h1>Матчи и контекст.<br />Без догадок.</h1>
        <p className="lead">
          Актуальный каталог спортивных событий — основа для статистики,
          новостей и объяснимого AI-анализа.
        </p>
      </section>

      <section className="catalog-section">
        <header>
          <div>
            <p className="eyebrow">БЛИЖАЙШИЕ СОБЫТИЯ</p>
            <h2>Матчи</h2>
          </div>
          <span className="timezone">Время указано локально</span>
        </header>
        <EventCatalog />
      </section>

      <footer>
        bet.score предоставляет аналитическую информацию и не призывает делать ставки.
      </footer>
    </main>
  );
}
