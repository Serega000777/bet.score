CREATE TABLE data_provider (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key text NOT NULL UNIQUE,
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE provider_competition (
  provider_id uuid NOT NULL REFERENCES data_provider(id),
  external_id text NOT NULL,
  competition_id uuid NOT NULL REFERENCES competition(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider_id, external_id),
  UNIQUE (provider_id, competition_id)
);

CREATE TABLE provider_team (
  provider_id uuid NOT NULL REFERENCES data_provider(id),
  external_id text NOT NULL,
  team_id uuid NOT NULL REFERENCES team(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider_id, external_id),
  UNIQUE (provider_id, team_id)
);

CREATE TABLE provider_event (
  provider_id uuid NOT NULL REFERENCES data_provider(id),
  external_id text NOT NULL,
  event_id uuid NOT NULL REFERENCES sporting_event(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider_id, external_id),
  UNIQUE (provider_id, event_id)
);

CREATE TABLE provider_event_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL REFERENCES data_provider(id),
  external_event_id text NOT NULL,
  event_id uuid NOT NULL REFERENCES sporting_event(id),
  version text NOT NULL,
  observed_at timestamptz NOT NULL,
  checksum char(64) NOT NULL,
  payload jsonb NOT NULL,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider_id, external_event_id, version),
  CHECK (jsonb_typeof(payload) = 'object')
);

CREATE INDEX provider_event_snapshot_event_idx
  ON provider_event_snapshot(event_id, observed_at DESC);
