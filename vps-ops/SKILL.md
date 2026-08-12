---
name: vps-ops
description: >
  Эксплуатация Python-приложений на одиночном VPS без Docker (nginx +
  systemd + postgres + redis), три режима: deploy — unit-файл, server-блок,
  TLS, бэкапы, firewall и аудит существующего деплоя; observe — Sentry,
  healthcheck, структурные логи в journald, алерты на диск/память/TLS;
  triage — идущий инцидент (рестарт-луп, 502/504, диск заполнен, postgres не
  принимает соединения, бот молчит). Используй когда пользователь говорит
  «прод лежит», «502», «диск заполнился», «nginx: configuration file test
  failed», «как узнать, что прод упал», «хочу перевести логи на JSON»,
  «создаём скрипт бэкапа базы», просит unit-файл или конфиг nginx. Медленные
  запросы — postgres-performance.
metadata:
  version: 1.1.1
  verified: 2026-08-10
---

# VPS Ops

Один сервер, без Docker: nginx + systemd + postgres + redis. Конфиги пишутся
локально, применяются на Linux-сервере. Цель — конфигурация, которая переживает
рестарт и ребут, не теряет данные, не светит секреты, и о поломке которой ты
узнаёшь раньше пользователей.

## Шаг 0. Выбери режим

| Режим | Когда | Куда дальше |
|---|---|---|
| **deploy** | сервис едет на сервер; или «проверь мой деплой» | разделы «Контекст» → «Риски» → справочники конфигов |
| **observe** | «как я узнаю, что прод упал»; наблюдаемости нет или она дырявая | [references/observability.md](references/observability.md) |
| **triage** | прод уже сломан, нужна причина | [references/triage.md](references/triage.md) — **сначала улики, потом рестарт** |

Режим не всегда назван прямо. «Сервис падает после рестарта» — это deploy
(конфиг), а не triage. «Сервис упал час назад, что случилось» — triage.
Если инцидент уже потушен и вопрос «как не проспать следующий» — observe.

При инциденте не начинай с чтения конфигов: открой triage и собери улики,
пока состояние процесса живо.

## Контекст — установить ПЕРВЫМ делом (для любого режима)

1. **Тип приложения** — Django (gunicorn/WSGI или uvicorn/ASGI), FastAPI
   (uvicorn), aiogram-бот (polling-воркер, без HTTP). Определяет unit, нужен ли
   nginx и есть ли вообще healthcheck-эндпоинт.
2. **Привязка процесса** — unix-socket (предпочтительно за nginx) или TCP-порт.
3. **Внешние зависимости** — postgres и/или redis; нужны ли в `After=` юнита.
4. **Домен и TLS** — есть ли домен под certbot; HTTP-only в проде недопустим.
5. **Сервисный пользователь** — НЕ root, отдельный системный пользователь.
6. **Что уже есть** — не дублируй: `grep` по проекту (`sentry_sdk`, `LOGGING`,
   `/health`), `systemctl cat`, `/etc/nginx/`, cron/таймеры.

## Режим deploy

1. Собери факты: unit-файлы (`/etc/systemd/system/*.service`),
   `systemctl status`, server-блоки nginx, конфиги postgres/redis, бэкапы,
   `ufw status`, под кем запускается процесс, где лежат секреты.
2. Прогони чеклист ниже и справочники конфигов.
3. Классифицируй риск и объясни, *что именно* отвалится на его сетапе.
4. Выдай рабочий конфиг или правку; для аудита — отчёт по
   [references/output-format.md](references/output-format.md).

### Чеклист (детали — в справочниках)

- Сервис под **не-root** пользователем, `Restart=always`, `enable`-нут (поднимется после ребута)?
- `TimeoutStopSec` хватает на graceful shutdown (gunicorn/uvicorn/бот закрывают пулы и сессии)?
- Секреты в `EnvironmentFile` (права `600`, владелец — сервис), а НЕ в репо и не в строке unit?
- HTTP за nginx: TLS с автопродлением, редирект 80→443, security-заголовки, gzip?
- nginx проксирует на **unix-socket**, статика и медиа отдаются nginx, а не приложением?
- postgres: отдельные пользователь и БД, `pg_hba` без `trust`, **проверенный** бэкап `pg_dump` по расписанию?
- redis: `bind 127.0.0.1`, `maxmemory` + policy (если cache), persistence (если broker/FSM)?
- Firewall: открыты только 22/80/443; БД и redis не смотрят наружу?
- Число воркеров согласовано с CPU и с `max_connections` postgres?
- Миграции при деплое применяются безопасно (→ `migration-safety-auditor`)?

## Уровни риска (общие для deploy и observe)

- **CRITICAL** — потеря данных или сервис уязвим: нет бэкапов postgres (или они
  ни разу не восстанавливались), сервис/postgres/redis слушает `0.0.0.0` без
  firewall, секреты в репозитории, приложение под root, нет TLS, ошибок не видно
  вообще (ни Sentry, ни доступных логов).
- **HIGH** — сервис падает и не встаёт, или падение заметят пользователи: нет
  `Restart=always`, не `enable`-нут, redis без `maxmemory` как cache (OOM),
  куцый `TimeoutStopSec` рвёт graceful shutdown, `max_connections` не согласован
  с воркерами, нет liveness-проверки.
- **MEDIUM** — нет security-заголовков и `server_tokens off`, бэкап без
  `lock_timeout` и не в off-peak, redis без persistence там, где он broker/FSM,
  нет лимитов ресурсов юнита, дефолтные таймауты nginx, нет ротации логов и
  алертов на ресурсы, нет fail2ban/rate-limit на SSH.
- **LOW** — именование юнитов, стиль, мелкие улучшения логирования.

## После инцидента

1. Короткий постмортем: симптом → причина → фикс → как не допустить (в docs
   проекта или Obsidian).
2. Пользователи заметили раньше тебя → режим **observe**: какой слой поймал бы.
3. Причина в конфиге (нет `Restart=`, лимитов, ротации) → режим **deploy**.

## Связь с библиотекой навыков

- `migration-safety-auditor` — применение миграций в процессе деплоя.
- `postgres-performance` — причина в медленных запросах, а не в падении.
- `aiogram-bot-auditor` — систематические проблемы бота после тушения пожара.
- `python-project-audit` — готовность самого кода к проду перед деплоем.
- `harness-engineering` — зафиксировать процедуру деплоя в Makefile/runbook и DoD.

## Справочники

- [references/systemd.md](references/systemd.md) — unit-файлы для gunicorn,
  uvicorn и polling-бота; `Restart`, `TimeoutStopSec`, `EnvironmentFile`,
  не-root, sandboxing, число воркеров.
- [references/nginx.md](references/nginx.md) — reverse-proxy, TLS (certbot),
  80→443, статика и медиа, gzip, таймауты, security-заголовки.
- [references/postgres-redis.md](references/postgres-redis.md) — пользователь и
  БД, `pg_hba`, `max_connections`, бэкап с проверкой восстановления; redis:
  `bind`, `maxmemory`, RDB/AOF под cache против broker/FSM.
- [references/security.md](references/security.md) — не-root, ufw, секреты,
  least privilege, SSH-hardening, fail2ban, права на файлы, обновления.
- [references/observability.md](references/observability.md) — режим observe:
  четыре слоя (Sentry, liveness, логи, ресурсные алерты), генерация и аудит.
- [references/triage.md](references/triage.md) — режим triage: дерево симптомов,
  быстрая триада команд, чеклист «собрать до рестарта».
- [references/output-format.md](references/output-format.md) — формат отчёта аудита.
