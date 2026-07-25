# Начальная модель данных

```mermaid
erDiagram
  USER ||--o{ SUBSCRIPTION : owns
  USER ||--o{ USER_SESSION : authenticates
  SPORT ||--o{ COMPETITION : contains
  COMPETITION ||--o{ EVENT : schedules
  SPORT ||--o{ TEAM : categorizes
  TEAM ||--o{ EVENT_PARTICIPANT : participates
  EVENT ||--o{ EVENT_PARTICIPANT : has
  EVENT ||--o{ EVENT_SNAPSHOT : captures
  EVENT ||--o{ NEWS_LINK : references
  NEWS_ARTICLE ||--o{ NEWS_LINK : links
  EVENT_SNAPSHOT ||--o{ ANALYSIS : grounds
  ANALYSIS ||--o{ ANALYSIS_SOURCE : cites
  PROVIDER ||--o{ EVENT_SNAPSHOT : supplies

  EVENT {
    uuid id PK
    string provider_key UK
    timestamptz starts_at
    string status
  }
  USER_SESSION {
    uuid id PK
    uuid user_id FK
    bytes token_hash UK
    timestamptz expires_at
    boolean revoked
  }
  TEAM {
    uuid id PK
    uuid sport_id FK
    string name
    string short_name
  }
  EVENT_PARTICIPANT {
    uuid event_id FK
    uuid team_id FK
    string role
    int score
  }
  EVENT_SNAPSHOT {
    uuid id PK
    uuid event_id FK
    int version
    jsonb payload
    timestamptz observed_at
  }
  ANALYSIS {
    uuid id PK
    uuid snapshot_id FK
    string model
    string prompt_version
    jsonb result
    decimal confidence
  }
```

Физическая схема каталога уже хранит канонические команды, соревнования и события. Роль участника уникальна внутри матча, поэтому событие не может получить двух хозяев или двух гостей. Provider-specific идентификаторы будут добавлены отдельной таблицей соответствий после выбора поставщика.
