# Деплой ботов: polling под systemd (основное) + webhook (best practice)

Профиль владельца: деплой через systemd + nginx + redis + postgres, основной режим — polling.

## Polling под systemd (основной сценарий)

Бот — это long-running воркер, не HTTP-сервис. Юнит-файл `/etc/systemd/system/mybot.service`:

```ini
[Unit]
Description=mybot (aiogram)
After=network-online.target redis-server.service postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=mybot                      # не root
WorkingDirectory=/opt/mybot
EnvironmentFile=/opt/mybot/.env # BOT_TOKEN и секреты здесь, не в репозитории
ExecStart=/opt/mybot/.venv/bin/python -m bot
Restart=always
RestartSec=3
TimeoutStopSec=30               # дать graceful shutdown закрыть сессии/redis

[Install]
WantedBy=multi-user.target
```

Критично:
- **Один экземпляр.** Не клонируй юнит и не запускай вторую копию с тем же токеном → 409 Conflict.
- `Restart=always` поднимает после краша; но это не замена обработке ошибок.
- systemd шлёт SIGTERM при `restart/stop` — бот должен чисто завершиться (graceful shutdown,
  см. reliability.md). `TimeoutStopSec` даёт на это время.
- Логи идут в journald (`journalctl -u mybot`), если пишешь в stdout/stderr.

## RedisStorage для FSM (прод)

`MemoryStorage` теряет состояние при каждом рестарте/деплое. В проде — Redis:

```python
from aiogram.fsm.storage.redis import RedisStorage
storage = RedisStorage.from_url("redis://localhost:6379/0")
dp = Dispatcher(storage=storage)
```

Redis тут же может служить для троттлинга, кэша и фоновых очередей. Один redis, разные БД-индексы
по назначению.

## Секреты

- `BOT_TOKEN` и прочее — через `EnvironmentFile`/env, читать `config.py` (pydantic-settings).
- Токен в репозитории/в коде — утечка; при компрометации немедленно отозвать у @BotFather.
- `.env` — в `.gitignore`, права `600`, владелец — сервисный пользователь.

## Логирование и наблюдаемость

- Структурные логи в stdout → journald. Уровень настраиваемый из env.
- Логируй ошибки Telegram и необработанные исключения (глобальный `@dp.errors()`).
- Для алертов — Sentry (`sentry-sdk`) ловит необработанные исключения хендлеров.
- Healthcheck для polling: systemd watchdog (`WatchdogSec=` + `sd_notify`) или внешний пинг
  «бот жив» (например, периодическая запись в redis с TTL, мониторинг ключа).

## Webhook (best practice на будущее)

Когда понадобится webhook (масштаб, отсутствие исходящих long-poll): aiohttp-приложение за
nginx с TLS.

```python
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path="/webhook")
setup_application(app, dp, bot=bot)
# на старте: await bot.set_webhook(URL, secret_token=WEBHOOK_SECRET,
#                                  drop_pending_updates=True, allowed_updates=...)
```

Критично для webhook:
- **`secret_token`** обязателен: Telegram шлёт его в заголовке `X-Telegram-Bot-Api-Secret-Token`,
  `SimpleRequestHandler` проверяет — защита от поддельных запросов на твой эндпоинт.
- За nginx с валидным TLS; наружу только HTTPS. nginx проксирует на локальный порт aiohttp.
- Один webhook-URL на бота. Не держи одновременно polling и webhook.
- `drop_pending_updates` при установке — осознанно (сбросит накопленное за простой).
- Это уже HTTP-сервис → деплой ближе к веб-стеку (uvicorn/gunicorn не нужен, aiohttp сам сервер),
  но под systemd так же, с healthcheck-эндпоинтом.

## Polling vs webhook — кратко

| | Polling | Webhook |
|--|---------|---------|
| Инфраструктура | минимум (исходящие запросы) | публичный HTTPS, TLS, nginx, secret |
| Масштаб | один процесс | можно масштабировать приёмник |
| Когда | по умолчанию, MVP, небольшие боты | высокая нагрузка, нет исходящего long-poll |
