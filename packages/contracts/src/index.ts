export type EventStatus = 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled';

export type Participant = {
  id: string;
  name: string;
  short_name: string;
  role: 'home' | 'away';
  score: number | null;
};

export type SportingEvent = {
  id: string;
  sport: string;
  competition_id: string;
  competition: string;
  country_code: string | null;
  starts_at: string;
  status: EventStatus;
  home: Participant;
  away: Participant;
};

export type EventList = {
  items: SportingEvent[];
  count: number;
};

export type EventProvenance = {
  provider_key: string;
  version: string;
  observed_at: string;
  ingested_at: string;
  checksum: string;
};

export type EventProvenanceList = {
  items: EventProvenance[];
  count: number;
};

export type EventUpdated = {
  type: 'event.updated';
  protocol_version: 1;
  event_id: string;
};

export const statusLabels: Record<EventStatus, string> = {
  scheduled: 'Скоро',
  live: 'LIVE',
  finished: 'Завершён',
  postponed: 'Перенесён',
  cancelled: 'Отменён',
};
