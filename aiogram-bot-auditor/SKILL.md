---
name: aiogram-bot-auditor
description: >
  Аудит и помощь по Telegram-ботам на aiogram 3.x: надёжность Telegram API, архитектура,
  деплой и тесты. Находит необработанный flood-control (429/TelegramRetryAfter), несколько
  polling-инстансов (409 Conflict), блокировку event loop, MemoryStorage в проде, отсутствие
  graceful shutdown и идемпотентности, проблемы структуры (Router/middlewares/FSM) и
  небезопасный webhook. Используй когда пользователь просит проверить или отревьюить бота,
  спрашивает «почему бот падает/тормозит/дублирует ответы», пишет или чинит aiogram-бота,
  настраивает FSM/middlewares/webhook/деплой или рассылку, или упоминает aiogram,
  TelegramRetryAfter, RedisStorage, polling/webhook. Только aiogram 3.x.
metadata:
  version: 1.0.0
---

# Aiogram Bot Auditor

Аудитор и помощник по Telegram-ботам на **aiogram 3.x**. Цель — поймать то, из-за чего бот в
проде падает, тормозит, дублирует ответы, теряет состояние или попадает под флуд-бан, а также
выправить структуру и тесты. По итогу — отчёт с уровнями риска и (по согласованию) правки.

## Когда применять

Перед деплоем бота, при ревью PR, при жалобах «бот не отвечает / тормозит / дублирует / теряет
шаг диалога», при настройке рассылки, FSM, middlewares, webhook. Только aiogram 3.x — если код
на 2.x (`executor`, `Dispatcher(bot)`, `@dp.message_handler`), сначала предупреди о
несовместимости и предложи миграцию на 3.x, не применяй 3.x-советы вслепую.

## Контекст — установить ПЕРВЫМ делом

1. **Версия aiogram** — подтверди 3.x (импорты `from aiogram import Router, F`, `dp.run_polling`).
2. **Запуск** — polling (по умолчанию у владельца) или webhook. См. [references/deploy.md](references/deploy.md).
3. **Storage FSM** — MemoryStorage (только dev) или RedisStorage (прод). У владельца есть redis.
4. **Масштаб** — есть ли рассылки/большая аудитория (тогда критичен flood-control и троттлинг).
5. **Инстансы** — гарантирован ли один polling-процесс (две копии → 409 Conflict).

## Процесс

1. Собрать точки входа (`__main__`, создание `Bot`/`Dispatcher`, `run_polling`/webhook-setup),
   роутеры, middlewares, FSM, обработку ошибок, места `bot.send_*`/рассылок, деплой-юнит.
2. Прогнать по чеклисту рисков (ниже) и справочникам.
3. Классифицировать риск, объяснить *почему* ломается в проде именно у него.
4. Предложить безопасную альтернативу.
5. Отчёт по [references/output-format.md](references/output-format.md); по согласованию — правки.

## Уровни риска

- **CRITICAL** — бот не работает/недоступен в проде: две polling-копии (409), блокировка
  event loop (sync/CPU в хендлере), краш без graceful shutdown с потерей состояния.
- **HIGH** — рассылка без обработки `TelegramRetryAfter` (429) и `TelegramForbiddenError`
  (бот заблокирован) → бан токена/потеря сообщений; MemoryStorage в проде (теряет FSM при
  рестарте); глобально не обработанные `TelegramAPIError`.
- **MEDIUM** — нет идемпотентности к повторной доставке апдейтов, нет таймаутов, токен/секреты
  в репозитории, `allowed_updates` не включает нужные типы, монолит без роутеров/middlewares.
- **LOW** — стиль, именование, мелкие улучшения.

## Быстрый чеклист

- Гарантирован **один** polling-инстанс? (две копии → 409, апдейты теряются)
- Рассылка ловит `TelegramRetryAfter` и `TelegramForbiddenError`, троттлит (≤~30 msg/s, ~1/s в чат)?
- В хендлерах нет блокирующих/CPU-операций в event loop (sync-БД, requests, тяжёлые вычисления)?
- FSM на **RedisStorage** в проде, а не MemoryStorage?
- Есть graceful shutdown: `dp.shutdown`, закрытие `bot.session`, redis, пулов БД?
- `allowed_updates` включает нужные типы (`callback_query`, `my_chat_member` и т.п.)?
- Токен и секреты — из env/`EnvironmentFile`, не в репозитории?
- Хендлеры идемпотентны к повторной доставке (особенно платежи/побочные эффекты)?
- Webhook (если есть): проверяется `secret_token`, за nginx+TLS, `drop_pending_updates` осознанно?

## Связь с библиотекой навыков

- Бот ходит в БД с миграциями → перед деплоем навык **`migration-safety-auditor`**.
- Аудит/написание тестов хендлеров и FSM → **`test-coverage-auditor`** (см. также
  [references/testing.md](references/testing.md)).
- Ревью диффа правок → **`techlead-ai`**; перед релизом → **`python-project-audit`**.

## Справочники

- [references/reliability.md](references/reliability.md) — Telegram API: 429/flood-control,
  ошибки, троттлинг рассылок, таймауты, graceful shutdown, идемпотентность, single instance.
- [references/architecture.md](references/architecture.md) — Router, middlewares (outer/inner),
  DI, FSM и storage, фильтры (`F`), структура проекта, вынос бизнес-логики из хендлеров.
- [references/deploy.md](references/deploy.md) — polling под systemd (основное), webhook+nginx
  (best practice), RedisStorage, секреты, логирование, healthcheck, один экземпляр.
- [references/testing.md](references/testing.md) — pytest, мок `Bot`, `feed_update`, тесты
  хендлеров и переходов FSM.
- [references/output-format.md](references/output-format.md) — формат отчёта.
