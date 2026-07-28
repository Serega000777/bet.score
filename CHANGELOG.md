# Журнал изменений

Все существенные изменения проекта фиксируются в этом файле. Формат основан на Keep a Changelog, версии следуют Semantic Versioning.

## [Unreleased]

- Добавлены восстановление сохранённого состояния и отдельная подборка матчей в Telegram Mini App.
- Добавлены авторизованные сохранённые матчи и управление ими из Telegram Mini App.
- Добавлены API и интерфейс навигации по видам спорта и соревнованиям с фильтрацией каталога матчей.
- Добавлены измеримые SLO, Prometheus alert rules и monitoring-профиль.
- Добавлены масштабируемые Prometheus-метрики transactional outbox.
- Добавлен transactional outbox для надёжной доставки ingestion → Redis.
- Добавлены heartbeat, лимиты и bounded-метрики LIVE WebSocket-соединений.
- Добавлен безопасный LIVE-канал Redis Pub/Sub → WebSocket → Telegram Mini App.
- Добавлен readiness-контроль PostgreSQL и Redis с ограниченным временем ожидания.
- Добавлены безопасные request ID, access-log и Prometheus-совместимые HTTP-метрики.

### Добавлено

- фундамент монорепозитория bet.score;
- Project Bible, PRD, roadmap, архитектура и журнал решений;
- каркасы FastAPI, Next.js и Telegram Mini App;
- локальная инфраструктура PostgreSQL, Redis и Nginx;
- базовый CI, правила форматирования и линтинга;
- начальная ER-диаграмма и OpenAPI-контракт health endpoint.
- канонический каталог матчей с командами, соревнованиями и статусами событий;
- PostgreSQL-адаптер каталога на SQLAlchemy и асинхронном asyncpg;
- API списка ближайших матчей и карточки отдельного события;
- адаптивный web-каталог с состояниями загрузки, ошибки, пустого результата и успеха;
- локальные демонстрационные данные, изолированные от будущего ingestion-провайдера.
- серверная проверка Telegram Mini App `initData` с контролем подписи и свежести;
- непрозрачные cookie-сессии, хранение только SHA-256 hash и серверный logout;
- экраны авторизации Telegram Mini App без небезопасного browser bypass;
- последовательный migration runner с checksum и PostgreSQL advisory lock.
- provider-neutral ingestion-ядро с атомарной нормализацией событий;
- таблицы сопоставления внешних ID и неизменяемые snapshots provenance;
- обязательный PostgreSQL integration-тест идемпотентности ingestion в CI.
- авторизованный каталог матчей в Telegram Mini App;
- мобильные состояния загрузки, ошибки с повтором, пустого каталога и списка событий.
- фактическая карточка матча в Telegram Mini App с отдельными состояниями 404 и временной ошибки;
- честное состояние ожидания AI-анализа без генерации неподтверждённых выводов.
- безопасный provenance API без raw provider payload и внешних идентификаторов;
- отображение источника, версии, времени наблюдения и checksum в карточке Mini App.
