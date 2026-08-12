# README

README — первое, что увидит новый человек в проекте, будущий ты через полгода и агент в первой
сессии. Цель — за минуту понять, что это, как запустить локально и как оно деплоится. Никакой
маркетинговой воды, бейджей ради бейджей и раздела «Contributing», если контрибьюторов не ждут.

## Что включать (и что НЕ включать)

**Включать:** назначение в 1–2 строки · быстрый старт · полный список env · команды запуска
(dev и прод) · короткую деплой-заметку · ссылку на архитектуру (если есть).

**НЕ включать:** длинное вступление «в современном мире…», скриншоты ради красоты, раздел
Contributing/Code of Conduct там, где контрибьюторов не ждут, перечисление того, что и так видно в коде,
дублирование `requirements.txt`/`pyproject.toml`.

## Структура (порядок важен — сверху самое нужное)

```markdown
# Project Name

Одна-две строки: что это и какую задачу решает. Без воды.
Пример: «FastAPI-сервис, считающий аналитику по заказам и отдающий её боту. Internal, не публичный.»

## Стек

Python 3.12 · FastAPI · Postgres · Redis · деплой: systemd + nginx. (Кратко, для ориентира.)

## Быстрый старт

```bash
git clone <url> && cd project
uv sync                      # или: python -m venv .venv && pip install -e .
cp .env.example .env         # заполнить переменные (см. ниже)
alembic upgrade head         # миграции
uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная       | Обязательна | По умолчанию | Назначение                      |
|------------------|-------------|--------------|---------------------------------|
| `DATABASE_URL`   | да          | —            | DSN Postgres                    |
| `REDIS_URL`      | да          | —            | Redis для кэша/очередей         |
| `BOT_TOKEN`      | да          | —            | токен Telegram-бота             |
| `LOG_LEVEL`      | нет         | `INFO`       | уровень логирования             |

> Список должен совпадать с `.env.example` и с тем, что реально читает код (`config.py`,
> `pydantic-settings`). Это аудитируется — устаревший список env = CRITICAL.

## Запуск

- **dev:** `uvicorn app.main:app --reload`
- **прод:** под systemd, см. деплой-заметку ниже.
- **бот:** `python -m bot`
- **миграции:** `alembic upgrade head` (Django: `python manage.py migrate`)

## Деплой (заметка для будущего себя)

- Юнит: `/etc/systemd/system/project.service` → `ExecStart=.../gunicorn app.main:app -k uvicorn...`.
- Секреты — через `EnvironmentFile=/etc/project/.env`, НЕ в репозитории.
- nginx: reverse-proxy на `127.0.0.1:8000`, TLS, статика отдаётся напрямую.
- Перезапуск: `sudo systemctl restart project`. Логи: `journalctl -u project -f`.
- Зависимости: postgres, redis. Перед миграциями на проде — навык `migration-safety-auditor`.

## Архитектура

См. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) и решения в [docs/adr/](docs/adr/).
```

## Заметки по адаптации под профиль

- **Django:** quick start = `migrate` + `createsuperuser` + `runserver`; прод — gunicorn/uvicorn
  workers под systemd, `collectstatic`, settings через env. Упомяни `DJANGO_SETTINGS_MODULE`.
- **FastAPI:** dev — `--reload`; прод — gunicorn с uvicorn-воркерами под systemd за nginx.
- **aiogram-бот:** запуск `python -m bot`; деплой — отдельный systemd-юнит; storage Redis в проде;
  гарантировать один polling-инстанс (см. навык `aiogram-bot-auditor`).
- **automation-скрипт:** что делает, как запускается из cron/systemd-timer, какие входы/выходы.

## Деплой-заметка vs полный runbook

README хранит **минимальную** деплой-заметку — «как перезапустить и где логи». Если деплой сложный
(несколько сервисов, последовательность миграций, откат) — вынеси в `docs/DEPLOY.md` и сошлись на
него. README не должен превращаться в runbook.

## Анти-паттерны

- README, который противоречит коду (команда не работает, env переименована) — хуже пустого.
- «TODO: написать документацию» месяцами — лучше 10 честных строк, чем заглушка.
- Дублирование кода/конфигов в README: они разъедутся. Ссылайся, не копируй (кроме `.env.example`).
- Описание внутренней реализации в README — это для ARCHITECTURE.md/docstrings, не для README.
