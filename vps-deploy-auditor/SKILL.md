---
name: vps-deploy-auditor
description: >
  Деплой Python-приложений на VPS без Docker и аудит существующего деплоя: nginx + systemd +
  redis + postgresql. Покрывает Django (gunicorn/uvicorn), FastAPI (uvicorn-воркеры),
  aiogram-боты (polling-воркер) под systemd; nginx reverse-proxy с TLS (certbot), статикой,
  таймаутами и security-заголовками; postgres (отдельный пользователь/БД, бэкапы pg_dump,
  лимиты соединений); redis (cache/broker/FSM, persistence, maxmemory); безопасность хоста
  (не-root, ufw, секреты в EnvironmentFile, fail2ban). Режимы: генерация шаблонов конфигов
  и аудит с уровнями риска. Используй когда пользователь деплоит Django/FastAPI/бота на VPS,
  просит unit-файл, конфиг nginx, настройку systemd/postgres/redis, бэкап БД, проверить или
  отревьюить деплой, спрашивает «как задеплоить без Docker», «безопасен ли мой сервер»,
  «почему сервис падает после рестарта», или упоминает gunicorn, uvicorn, certbot, ufw, systemd.
metadata:
  version: 1.0.0
---

# VPS Deploy Auditor

Помощник по деплою Python-приложений на одиночный VPS **без Docker** (nginx + systemd + redis +
postgres) и аудитор существующего деплоя. Цель — рабочая, безопасная и переживающая рестарт
конфигурация: сервис не падает молча, переживает ребут, отдаёт TLS, не теряет состояние и не
светит секреты. По итогу — либо сгенерированные шаблоны конфигов, либо отчёт с уровнями риска.

## Два режима

- **Генерация** — создать рабочие шаблоны (unit-файл, server-блок nginx, cron-бэкап, настройку
  redis/postgres) под конкретный тип приложения. См. справочники, бери шаблоны как основу.
- **Аудит** — пройтись по существующему деплою, классифицировать риски, объяснить, что отвалится
  на проде или при рестарте. Отчёт по [references/output-format.md](references/output-format.md).

## Контекст — установить ПЕРВЫМ делом

1. **Тип приложения** — Django (WSGI/gunicorn или ASGI/uvicorn), FastAPI (ASGI/uvicorn),
   aiogram-бот (polling-воркер, без HTTP). От этого зависит unit и нужен ли nginx.
2. **Привязка процесса** — unix-socket (предпочтительно для HTTP за nginx) или TCP-порт.
3. **Внешние зависимости** — postgres и/или redis; нужны ли в `After=` юнита.
4. **Домен и TLS** — есть ли домен под certbot; HTTP-only недопустим в проде.
5. **Сервисный пользователь** — НЕ root; отдельный системный пользователь под приложение.

## Процесс

1. Собрать факты: unit-файлы (`/etc/systemd/system/*.service`), `systemctl status`, server-блоки
   nginx (`/etc/nginx/`), конфиги postgres/redis, cron/таймеры бэкапов, `ufw status`, под кем
   и откуда запускается процесс, где лежат секреты.
2. Прогнать по чеклисту рисков (ниже) и справочникам.
3. Классифицировать риск, объяснить *почему* ломается у него (одиночный VPS, соло-эксплуатация).
4. Предложить рабочий конфиг/правку.
5. Режим генерации — выдать шаблоны; режим аудита — отчёт по output-format.md.

## Уровни риска

- **CRITICAL** — потеря данных или сервис недоступен/уязвим: нет бэкапов postgres (или они не
  проверены), сервис/postgres/redis слушает `0.0.0.0` без firewall, секреты закоммичены в репо,
  приложение работает под root, нет TLS на публичном HTTP.
- **HIGH** — сервис падает и не поднимается, или деградирует под нагрузкой: нет `Restart=always`,
  нет `WantedBy`/`enable` (не стартует после ребута), redis без `maxmemory`/policy как cache
  (OOM-kill), маленький/отсутствующий `TimeoutStopSec` рвёт graceful shutdown, postgres
  `max_connections` не согласован с числом воркеров (отказы соединений).
- **MEDIUM** — нет security-заголовков/`server_tokens off`, нет `lock_timeout` бэкапа в
  off-peak, redis без persistence там, где он broker/FSM, нет лимитов ресурсов юнита, gzip
  выключен, таймауты nginx по умолчанию, нет `fail2ban`/rate-limit на SSH/входы.
- **LOW** — стиль, именование юнитов, мелкие улучшения логирования/комментарии.

## Быстрый чеклист (детали — в справочниках)

- Сервис под **не-root** системным пользователем, `Restart=always`, `enable`-нут (стартует после ребута)?
- `TimeoutStopSec` достаточен для graceful shutdown (gunicorn/uvicorn/бот закрывают пулы/сессии)?
- Секреты в `EnvironmentFile` (права `600`, владелец — сервис), а НЕ в репо/в unit-строке?
- HTTP-приложения за nginx: TLS (certbot+auto-renew), редирект 80→443, security-заголовки, gzip?
- nginx проксирует на **unix-socket**, статика/медиа отдаются nginx (не приложением)?
- postgres: отдельные пользователь+БД, `pg_hba` без `trust`, есть **проверенный** `pg_dump`-бэкап по cron?
- redis: `bind 127.0.0.1`, `maxmemory`+policy (если cache), persistence (если broker/FSM)?
- Firewall (ufw): открыты только нужные порты (22/80/443), БД/redis не наружу?
- Число воркеров согласовано с CPU и с `max_connections` postgres?
- Миграции БД применяются при деплое безопасно (см. `migration-safety-auditor`)?

## Связь с библиотекой навыков

- Применение миграций в процессе деплоя → **`migration-safety-auditor`** (не уронить прод DDL).
- Готовность кода к проду перед деплоем (антипаттерны, безопасность, highload) → **`python-project-audit`**.
- Зафиксировать процедуру деплоя как заметку в репозитории (Makefile/runbook) → **`harness-engineering`**.
- Деплой aiogram-бота под systemd детальнее (single instance, FSM) → **`aiogram-bot-auditor`**.

## Справочники

- [references/systemd.md](references/systemd.md) — unit-файлы для gunicorn (Django WSGI),
  uvicorn (FastAPI/Django ASGI) и polling-бота; `Restart`, `TimeoutStopSec`, `EnvironmentFile`,
  не-root, sandboxing, socket-activation, число воркеров.
- [references/nginx.md](references/nginx.md) — reverse-proxy: TLS (certbot), 80→443, проксирование
  на socket/порт, статика/медиа, gzip, таймауты, размеры тела, security-заголовки.
- [references/postgres-redis.md](references/postgres-redis.md) — postgres: пользователь/БД,
  `pg_hba`, `max_connections`, бэкап pg_dump по cron + проверка восстановления; redis:
  `bind`, `maxmemory`+policy, RDB/AOF под cache vs broker/FSM.
- [references/security.md](references/security.md) — не-root, ufw, секреты в EnvironmentFile,
  least privilege, SSH-hardening, fail2ban, права на файлы, обновления.
- [references/output-format.md](references/output-format.md) — формат отчёта аудита.
