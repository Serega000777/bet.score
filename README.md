# bet.score

bet.score — платформа объяснимой спортивной аналитики на базе искусственного интеллекта. Продукт предоставляет статистику, новости, вероятностные оценки и аргументацию модели, но не призывает пользователей делать ставки.

## Статус

Технический фундамент завершён. Каталог спортивных событий проходит через PostgreSQL, FastAPI, web-интерфейс и Telegram Mini App. Telegram-клиент использует серверную проверку `initData` и отзывные cookie-сессии.

## Быстрый старт

Требования: Docker 27+, Docker Compose v2, Node.js 22+, pnpm 10+, Python 3.13+.

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- API: `http://localhost:8000/api/v1/health`
- Каталог API: `http://localhost:8000/api/v1/events`
- Web: `http://localhost:3000`
- Telegram Mini App: `http://localhost:3001`

## Структура

- `backend/` — FastAPI API и доменная логика;
- `frontend/` — основное веб-приложение;
- `telegram-mini-app/` — клиент Telegram;
- `mobile/` — границы будущих мобильных приложений;
- `database/` — модель данных и миграции;
- `docs/` — продуктовая и техническая документация;
- `prompts/` — версионируемые AI-промпты;
- `infrastructure/` — контейнеры и конфигурация окружений;
- `scripts/` — повторяемые инженерные операции.

Основные решения описаны в [Project Bible](docs/PROJECT_BIBLE.md), [PRD](docs/PRD.md) и [архитектуре](docs/ARCHITECTURE.md).

## Команды

```bash
pnpm install
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Backend запускается и проверяется отдельно из `backend/`; подробности находятся в его README.

При запуске Compose отдельный сервис `migrate` последовательно применяет миграции. В локальном окружении подключается `database/migrations/900_seed.sql`; при `APP_ENV=production` демонстрационный seed пропускается.

## Безопасность продукта

bet.score является аналитическим продуктом, а не сервисом ставок. Вероятностные оценки всегда сопровождаются источниками, временем актуальности и объяснением ограничений.
