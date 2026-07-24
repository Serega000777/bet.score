import React from 'react';

const capabilities = [
  'Актуальные данные о матчах',
  'Объяснимые выводы ИИ',
  'Новости и контекст события',
  'LIVE-обновления без визуального шума',
];

export default function HomePage() {
  return (
    <main>
      <nav><strong>bet.score</strong><span>Версия 0.1 · фундамент</span></nav>
      <section className="hero">
        <p className="eyebrow">AI SPORTS INTELLIGENCE</p>
        <h1>Спортивная аналитика,<br />которую можно проверить.</h1>
        <p className="lead">Статистика, новости и вероятностные оценки с понятным объяснением источников и ограничений модели.</p>
        <div className="notice">bet.score предоставляет аналитическую информацию и не призывает делать ставки.</div>
      </section>
      <section className="capabilities" aria-label="Возможности платформы">
        {capabilities.map((capability, index) => (
          <article key={capability}><span>0{index + 1}</span><h2>{capability}</h2><p>Компонент входит в утверждённую область MVP и будет реализован последовательным вертикальным срезом.</p></article>
        ))}
      </section>
    </main>
  );
}
