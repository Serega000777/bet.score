CREATE TABLE team (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sport_id uuid NOT NULL REFERENCES sport(id),
  name text NOT NULL,
  short_name varchar(32) NOT NULL,
  country_code char(2),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT team_sport_name_uq UNIQUE (sport_id, name)
);

CREATE INDEX team_sport_id_idx ON team(sport_id);

CREATE TABLE event_participant (
  event_id uuid NOT NULL REFERENCES sporting_event(id) ON DELETE CASCADE,
  team_id uuid NOT NULL REFERENCES team(id),
  role text NOT NULL CHECK (role IN ('home', 'away')),
  score integer CHECK (score IS NULL OR score >= 0),
  PRIMARY KEY (event_id, team_id),
  CONSTRAINT event_participant_event_role_uq UNIQUE (event_id, role)
);

CREATE INDEX event_participant_team_id_idx ON event_participant(team_id);
