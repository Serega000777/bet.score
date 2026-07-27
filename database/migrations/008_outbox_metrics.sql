CREATE TABLE outbox_delivery_stats (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  delivered bigint NOT NULL DEFAULT 0 CHECK (delivered >= 0),
  retries bigint NOT NULL DEFAULT 0 CHECK (retries >= 0),
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO outbox_delivery_stats(singleton, delivered, retries)
SELECT
  true,
  count(*) FILTER (WHERE delivered_at IS NOT NULL),
  COALESCE(
    sum(
      greatest(attempts - 1, 0)
      + CASE
          WHEN delivered_at IS NULL AND last_error_code IS NOT NULL THEN 1
          ELSE 0
        END
    ),
    0
  )
FROM event_outbox;

CREATE INDEX event_outbox_pending_created_idx
  ON event_outbox(created_at)
  WHERE delivered_at IS NULL;
