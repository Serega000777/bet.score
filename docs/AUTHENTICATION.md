# Авторизация и сессии

## Реализованный контур

Первый адаптер идентификации предназначен для Telegram Mini App. Клиент передаёт backend только необработанную строку `Telegram.WebApp.initData`. Поля `initDataUnsafe` никогда не считаются доверенными.

Проверка соответствует [официальной документации Telegram Mini Apps](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):

1. параметры сортируются по имени и объединяются переводом строки;
2. секрет вычисляется через HMAC-SHA-256 с ключом `WebAppData` и bot token;
3. подпись сравнивается constant-time операцией;
4. `auth_date` проверяется на максимальный возраст и дату из будущего;
5. только после проверки JSON пользователя преобразуется во внешнюю identity.

## Сессии

- клиент получает 256-битный непрозрачный token;
- PostgreSQL хранит только SHA-256 hash;
- cookie имеет `HttpOnly`, `SameSite=Lax`, `Path=/`;
- в staging/production cookie всегда имеет `Secure`;
- сессия имеет срок действия и может быть отозвана logout-операцией;
- изменение Telegram-профиля обновляет отображаемое имя, username и locale, но не создаёт дубликат пользователя.

## Конфигурация

- `TELEGRAM_BOT_TOKEN` — секрет бота, обязателен для endpoint;
- `TELEGRAM_INIT_DATA_TTL_SECONDS` — допустимый возраст `initData`, по умолчанию 600;
- `SESSION_COOKIE_NAME` — имя cookie;
- `SESSION_TTL_DAYS` — срок сессии, по умолчанию 30.

При отсутствии bot token endpoint возвращает HTTP 503. Секрет не передаётся клиенту и не записывается в логи.

## Следующие адаптеры

Web OIDC будет использовать тот же `IdentityRepository` и session core. Провайдер не выбирается до решения продуктовых вопросов по рынку и юридической модели.
