# systemd: unit-файлы для Python-приложений

systemd — общий знаменатель всех трёх классов: HTTP-сервис (Django/FastAPI) и polling-бот
запускаются как long-running процессы под одним механизмом. Файлы — в
`/etc/systemd/system/<name>.service`. После правок: `systemctl daemon-reload`, затем
`systemctl enable --now <name>`.

## Общие правила (для всех типов)

- **Не root.** Отдельный системный пользователь: `useradd --system --no-create-home --shell
  /usr/sbin/nologin appuser`. Файлы приложения принадлежат ему, `.venv` тоже.
- **Restart=always + RestartSec.** Поднимает после краша. Это НЕ замена обработке ошибок.
- **enable.** Без `WantedBy=multi-user.target` + `systemctl enable` сервис не стартует после ребута.
- **TimeoutStopSec.** Время на graceful shutdown (дренаж запросов, закрытие пулов/сессий).
  systemd шлёт SIGTERM, ждёт `TimeoutStopSec`, затем SIGKILL. Слишком мало → обрыв на лету.
- **EnvironmentFile.** Секреты из файла, не в `Environment=`-строках (видны в `systemctl show`).
- **Логи** идут в journald, если пишешь в stdout/stderr. Смотреть: `journalctl -u <name> -f`.

## Django через gunicorn (WSGI) — основной веб-сценарий

`/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=myapp (Django/gunicorn)
After=network-online.target postgresql.service redis-server.service
Wants=network-online.target

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/opt/myapp
EnvironmentFile=/opt/myapp/.env
ExecStart=/opt/myapp/.venv/bin/gunicorn config.wsgi:application \
    --workers 3 \
    --bind unix:/run/myapp/gunicorn.sock \
    --timeout 30 \
    --graceful-timeout 30 \
    --access-logfile - --error-logfile -
ExecReload=/bin/kill -s HUP $MAINPID
RuntimeDirectory=myapp                 # создаёт /run/myapp с нужными правами
Restart=always
RestartSec=3
TimeoutStopSec=35                       # > gunicorn --graceful-timeout

# sandboxing (least privilege)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/myapp /run/myapp    # куда можно писать (медиа, логи, сокет)

[Install]
WantedBy=multi-user.target
```

- `Type=notify` — gunicorn умеет sd_notify, systemd видит реальную готовность (с `gunicorn`
  достаточно дефолта; для notify установлен `gunicorn[setproctitle]` не обязателен, notify
  поддерживается из коробки). Если сомневаешься — `Type=simple`.
- `--bind unix:.../gunicorn.sock` — nginx проксирует на этот socket (быстрее и безопаснее порта).
- **Воркеры:** ориентир `2 * CPU + 1` для sync-воркеров. Согласуй с `max_connections` postgres
  (см. postgres-redis.md): `workers * (1 + макс. одновременных запросов БД на воркер)` ≤ лимита.
- `RuntimeDirectory=myapp` — `/run/myapp` создаётся при старте и чистится при стопе; не клади
  socket в `/tmp`.

## Django ASGI / FastAPI через uvicorn

ASGI (Django Channels, async-вьюхи, FastAPI). Для прода uvicorn запускают **под gunicorn** как
менеджер воркеров — он даёт перезапуск воркеров, graceful reload и notify:

```ini
ExecStart=/opt/myapp/.venv/bin/gunicorn config.asgi:application \
    --workers 3 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/run/myapp/uvicorn.sock \
    --timeout 30 --graceful-timeout 30 \
    --access-logfile - --error-logfile -
```

Для FastAPI — `app.main:app` вместо `config.asgi:application`. Чистый `uvicorn --workers N`
тоже работает (`ExecStart=.../uvicorn app.main:app --uds /run/myapp/uvicorn.sock --workers 3`),
но gunicorn-менеджер надёжнее для управления воркерами. Остальной unit — как у gunicorn выше.

- ASGI-воркеры держат много корутин на один процесс → воркеров обычно меньше (`CPU + 1` ... `2*CPU`),
  но каждый может открыть много соединений к БД — особенно следи за `max_connections`.

## aiogram-бот как polling-воркер (без HTTP)

Бот не слушает порт, nginx не нужен. Это long-running воркер:

```ini
[Unit]
Description=mybot (aiogram polling)
After=network-online.target redis-server.service postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/mybot
EnvironmentFile=/opt/mybot/.env        # BOT_TOKEN здесь, не в репо
ExecStart=/opt/mybot/.venv/bin/python -m bot
Restart=always
RestartSec=3
TimeoutStopSec=30                       # дать graceful shutdown закрыть session/redis/пулы
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mybot

[Install]
WantedBy=multi-user.target
```

- **Один экземпляр.** Не клонируй юнит и не запускай вторую копию с тем же токеном → 409 Conflict
  (детали — навык `aiogram-bot-auditor`). Polling нельзя масштабировать горизонтально.
- Graceful shutdown обязателен: на SIGTERM закрыть `bot.session`, redis, пулы БД (иначе утечки
  при каждом деплое). `TimeoutStopSec` даёт на это время.

## Socket-activation для HTTP (опционально)

Можно отдать сокет на управление systemd через `<name>.socket` (`ListenStream=/run/myapp/app.sock`)
+ `Requires=`/`After=` в юните. Это даёт стабильные права на сокет и старт по запросу, но для
одиночного always-on сервиса обычный `--bind unix:` + `RuntimeDirectory` проще и достаточно.

## Лимиты ресурсов (опционально, MEDIUM)

`MemoryMax=512M`, `CPUQuota=80%`, `LimitNOFILE=4096` в `[Service]` ограничивают аппетит сервиса —
полезно на маленьком VPS, чтобы один процесс не утянул весь хост. Ставь с запасом, по нагрузке.

## Частые ошибки (аудит)

- `Type=forking` без `PIDFile` → systemd теряет процесс. Для gunicorn/uvicorn — `notify`/`simple`.
- Нет `enable` → после ребута сервис мёртв (видно: активен сейчас, но `is-enabled` = disabled).
- Маленький `TimeoutStopSec` (< graceful-timeout приложения) → обрыв запросов при деплое.
- Секреты в `Environment=BOT_TOKEN=...` прямо в unit → видны всем через `systemctl show`.
- `ExecStart` от root без `User=` → приложение под root (CRITICAL, см. security.md).
