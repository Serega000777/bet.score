CREATE FUNCTION reject_provider_snapshot_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'provider event snapshots are immutable';
END;
$$;

CREATE TRIGGER provider_event_snapshot_immutable
BEFORE UPDATE ON provider_event_snapshot
FOR EACH ROW
EXECUTE FUNCTION reject_provider_snapshot_update();
