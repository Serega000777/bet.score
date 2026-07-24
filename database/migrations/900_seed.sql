-- Демонстрационные данные только для локальной разработки.
INSERT INTO sport (id, code, name)
VALUES ('10000000-0000-0000-0000-000000000001', 'football', 'Футбол')
ON CONFLICT (code) DO NOTHING;

INSERT INTO competition (id, sport_id, name, country_code)
VALUES (
  '20000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Демонстрационная лига',
  'RU'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO team (id, sport_id, name, short_name, country_code)
VALUES
  (
    '30000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    'Север',
    'SEV',
    'RU'
  ),
  (
    '30000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    'Восток',
    'VOS',
    'RU'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO sporting_event (id, competition_id, starts_at, status)
VALUES (
  '40000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000001',
  now() + interval '1 day',
  'scheduled'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO event_participant (event_id, team_id, role)
VALUES
  (
    '40000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000001',
    'home'
  ),
  (
    '40000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000002',
    'away'
  )
ON CONFLICT (event_id, team_id) DO NOTHING;
