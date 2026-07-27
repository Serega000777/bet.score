'use client';

import Link from 'next/link';
import { use } from 'react';

import { MatchDetail } from '../../../components/match-detail';

export default function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <main>
      <header>
        <Link className="brand-link" href="/">bet.score</Link>
        <span>КАРТОЧКА МАТЧА</span>
      </header>
      <MatchDetail eventId={id} />
      <footer>Факты и источники важнее уверенного тона.</footer>
    </main>
  );
}
