# SLO bet.score

## Область

Начальные SLO применяются к production API, LIVE invalidation и transactional
outbox. Окно расчёта — скользящие 30 дней. Пороговые значения пересматриваются
после появления фактического профиля нагрузки.

## Цели

| Контур | SLI | SLO |
|---|---|---|
| API | доля ответов без HTTP 5xx | 99,5% |
| API latency | p95 по HTTP histogram | не более 500 мс |
| Outbox | возраст старейшего pending при непустой очереди | не более 60 секунд |
| LIVE | доля handshake без отказа по capacity | 99,9% |

Для API availability 99,5% месячный error budget составляет примерно 3 часа
36 минут. При его исчерпании приоритет получают исправления надёжности, а
изменения, увеличивающие риск, откладываются.

## Алерты

Prometheus rules находятся в `infrastructure/monitoring/alerts.yml`. Critical
alerts: недоступность scrape, HTTP 5xx выше 1% и outbox старше 60 секунд.
Warning alerts: p95 выше 500 мс, частые retry, capacity выше 90% и отклонённые
LIVE-соединения.

Алерты не содержат UUID событий, IP пользователей, provider payload или секреты.
Маршруты метрик представлены только шаблонами FastAPI.

## Локальный запуск

```powershell
docker compose --profile monitoring up --build
```

Prometheus будет доступен на `http://localhost:9090`. Канал доставки уведомлений
оператору подключается отдельно для каждого окружения и не хранит секреты в
репозитории. В production Prometheus и `/api/v1/metrics` должны оставаться во
внутренней сети и не публиковаться через пользовательский ingress.
