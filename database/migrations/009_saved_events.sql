CREATE TABLE saved_event (
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  event_id uuid NOT NULL REFERENCES sporting_event(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, event_id)
);

CREATE INDEX saved_event_user_created_at_idx
  ON saved_event(user_id, created_at DESC);
