# postgres и redis на одиночном VPS

Обе службы — локальные, слушают только loopback, наружу не торчат. Главные риски: отсутствие
(или непроверенность) бэкапов postgres и redis-cache без лимита памяти.

## postgres: отдельные пользователь и БД

Никогда не подключай приложение под `postgres`-суперпользователем. Отдельные роль + БД:

```sql
CREATE USER myapp WITH PASSWORD 'СГЕНЕРИРОВАННЫЙ_ДЛИННЫЙ_ПАРОЛЬ';
CREATE DATABASE myapp OWNER myapp;
-- least privilege: приложению не нужен суперюзер/CREATEDB/CREATEROLE
```

Пароль — в `EnvironmentFile` приложения (`DATABASE_URL=postgres://myapp:...@127.0.0.1:5432/myapp`),
не в репозитории.

## postgres: доступ и сеть (pg_hba.conf, listen_addresses)

- `listen_addresses = 'localhost'` в `postgresql.conf` — БД не слушает внешний интерфейс.
- `pg_hba.conf`: локальные подключения по `scram-sha-256` (или `md5`), **никаких `trust`** для
  TCP. Пример строки: `host myapp myapp 127.0.0.1/32 scram-sha-256`.
- `trust` на `host`/публичном интерфейсе — CRITICAL: вход без пароля.
- Если БД всё же должна слушать сеть — закрыть порт 5432 в ufw для всех, кроме нужных IP.

## postgres: max_connections и воркеры

postgres держит процесс на каждое соединение; дефолт `max_connections = 100`. Считай:

```
пиковые соединения ≈ (gunicorn/uvicorn workers) × (соединений на воркер) + cron/боты/админ
```

- WSGI: обычно 1 активное соединение на воркер (+ пул). ASGI/async может открыть много на воркер.
- Если приложение использует пул (Django `CONN_MAX_AGE`, SQLAlchemy `pool_size`) — учитывай размер пула.
- Несогласованность → `FATAL: sorry, too many clients already` под нагрузкой (HIGH).
- На маленьком VPS лучше **пулер** (PgBouncer, transaction-mode) перед postgres, чем раздувать
  `max_connections` (каждое соединение ест RAM).

## postgres: базовый тюнинг (ориентир для VPS 2–4 ГБ RAM)

Стартовые значения, не догма — подбирай под профиль (например, через `PGTune`):

```conf
shared_buffers = 512MB           # ~25% RAM
effective_cache_size = 1536MB    # ~50–75% RAM (подсказка планировщику)
work_mem = 16MB                  # на операцию сортировки/хэша; осторожно × соединения
maintenance_work_mem = 128MB
wal_compression = on
```

`shared_buffers` слишком большой на маленьком хосте конкурирует с приложением за RAM — не жадничай.

## postgres: бэкап pg_dump по cron + ПРОВЕРКА восстановления

Бэкап, который ни разу не восстанавливали, — не бэкап. Скрипт `/opt/backup/pg_backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
DB=myapp
DIR=/var/backups/postgres
DATE=$(date +%F_%H%M)
mkdir -p "$DIR"
# -Fc = custom format (сжатый, для pg_restore выборочно)
pg_dump -U myapp -h 127.0.0.1 -Fc "$DB" > "$DIR/${DB}_${DATE}.dump"
# ротация: хранить 14 дней
find "$DIR" -name "${DB}_*.dump" -mtime +14 -delete
```

Cron от сервисного пользователя (`crontab -u postgres -e` или отдельного backup-юзера):

```cron
# каждый день в 03:30 (off-peak)
30 3 * * * /opt/backup/pg_backup.sh >> /var/log/pg_backup.log 2>&1
```

- Пароль для cron — в `~/.pgpass` (права `600`), не в командной строке.
- **Проверяй восстановление** (хотя бы раз): `pg_restore -d myapp_test /var/backups/.../X.dump`.
  Без проверки бэкап = CRITICAL (ложное чувство безопасности).
- **Off-site копия.** Бэкап на том же VPS не спасёт при гибели диска/хоста — копируй на внешнее
  хранилище (S3-совместимое, отдельный сервер).
- Альтернатива/дополнение для PITR — `pgBackRest`/WAL-архивирование; для соло-проекта обычно
  ежедневный `pg_dump` + off-site достаточно.

## redis: bind и доступ

```conf
bind 127.0.0.1 -::1          # ТОЛЬКО loopback; redis наружу = открытый ключ-доступ (CRITICAL)
protected-mode yes
# requirepass СГЕНЕРИРОВАННЫЙ_ПАРОЛЬ   # обязателен, если bind не только loopback
port 6379
```

Открытый в интернет redis без пароля — классический вектор взлома (запись cron/ключей). На
одиночном VPS — `bind 127.0.0.1` + ufw закрывает 6379 наружу.

## redis: cache vs broker/FSM — разные настройки persistence

Назначение определяет, нужна ли сохранность данных:

| Назначение | maxmemory | persistence | при рестарте |
|------------|-----------|-------------|--------------|
| **Cache** (Django cache, троттлинг) | обязателен + policy | можно выключить | данные восстановимы, можно терять |
| **Broker** (Celery) / **FSM-storage** бота | с запасом | нужна (AOF) | потеря = потерянные задачи/диалоги |

Cache:

```conf
maxmemory 256mb
maxmemory-policy allkeys-lru     # вытеснять давно неиспользуемое; БЕЗ лимита → OOM-kill (HIGH)
save ""                          # RDB не нужен чистому кэшу
```

Broker / FSM (нужна сохранность):

```conf
maxmemory 256mb
maxmemory-policy noeviction      # НЕ выбрасывать данные задач/состояния молча
appendonly yes                   # AOF — durability
appendfsync everysec
```

- Разделяй назначения по номерам БД (`redis://localhost:6379/0` cache, `/1` broker, `/2` FSM)
  или по инстансам, если настройки persistence конфликтуют.
- `maxmemory-policy noeviction` для broker/FSM: при заполнении redis вернёт ошибку на запись
  (видно), а не молча выбросит чужие задачи.

## Частые ошибки (аудит)

- Нет бэкапа postgres или он не проверен восстановлением — CRITICAL.
- postgres/redis слушают `0.0.0.0` без firewall — CRITICAL.
- `trust` в `pg_hba.conf` на TCP — CRITICAL.
- Приложение под postgres-суперпользователем — HIGH (least privilege).
- redis-cache без `maxmemory`/policy → OOM-kill всего хоста — HIGH.
- redis как broker/FSM без AOF → потеря задач/состояния при рестарте — HIGH.
- `max_connections` не согласован с воркерами → отказы соединений под нагрузкой — HIGH.
- Бэкап только на том же диске (нет off-site) — MEDIUM/HIGH в зависимости от ценности данных.
