ALTER TABLE competition
  ADD CONSTRAINT competition_identity_uq
  UNIQUE NULLS NOT DISTINCT (sport_id, name, country_code);
