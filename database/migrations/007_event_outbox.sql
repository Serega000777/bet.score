CREATE TABLE event_outbox (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_snapshot_id uuid NOT NULL UNIQUE REFERENCES provider_event_snapshot(id),
  event_id uuid NOT NULL REFERENCES sporting_event(id),
  event_type text NOT NULL CHECK (event_type = 'event.updated'),
  protocol_version smallint NOT NULL CHECK (protocol_version = 1),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at timestamptz NOT NULL DEFAULT now(),
  locked_until timestamptz,
  delivered_at timestamptz,
  last_error_code text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX event_outbox_pending_idx
  ON event_outbox(available_at, id)
  WHERE delivered_at IS NULL;
