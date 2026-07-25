ALTER TABLE app_user
  ADD COLUMN display_name text NOT NULL DEFAULT 'Пользователь',
  ADD COLUMN username text;

ALTER TABLE app_user
  ALTER COLUMN display_name DROP DEFAULT,
  ALTER COLUMN external_subject SET NOT NULL;

CREATE TABLE user_session (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  token_hash bytea NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  revoked boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX user_session_active_lookup_idx
  ON user_session(token_hash, expires_at)
  WHERE revoked = false;
