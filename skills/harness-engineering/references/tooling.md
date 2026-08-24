# Tooling — задачи-команды и CI под Python-стек

Стек известен: Python (Django / FastAPI / aiogram). Многостековые таблицы не нужны.
Инструменты по умолчанию: **ruff** (lint + format + security-правила `S`, нативная замена bandit),
**pytest** (+ pytest-django / httpx для FastAPI), **pip-audit** (supply-chain). Типизатор — **по
проекту, не хардкодь** (см. «Типизатор» ниже): `ty` (быстрый, без плагинов) или `mypy`+стабы.
Сначала **детектни, что реально установлено и проходит**, и подстрой цели под это.

## Runner: Makefile (кросс-платформенный)

Makefile — единый набор команд для тебя и для агента, одинаковый локально и в CI.

### `Makefile` (база, общая для всех Python-проектов)

```makefile
# подставь свой менеджер пакетов: uv run / poetry run / python -m
RUN := uv run

.PHONY: lint fmt fmt-check fix type test sec all
lint:      ; $(RUN) ruff check .
fmt:       ; $(RUN) ruff format .                 # ТОЛЬКО формат — без --fix (см. ниже)
fmt-check: ; $(RUN) ruff format --check .         # CI: упасть, если не отформатировано
fix:       ; $(RUN) ruff check --fix .            # автофикс ОТДЕЛЬНО и осознанно (см. ниже)
type:      ; $(RUN) ty check                      # ИЛИ mypy . — выбор типизатора см. ниже
test:      ; $(RUN) pytest -q
sec:       ; $(RUN) ruff check --select S . && $(RUN) pip-audit
all: lint type test sec
```

> **Почему `fmt` без `--fix`.** `ruff check --fix` сносит «неиспользуемые» импорты (F401). В Django
> такой импорт часто регистрирует сигналы/админку (side-effect) — слепой автофикс ломает регистрацию.
> Держи формат (`fmt`) и автофикс (`fix`) **раздельно**, F401 на Django-коде ревьюь руками.

> **`sec` = ruff `S` + pip-audit.** Ruff нативно реализует правила bandit как `S`
> (`ruff check --select S`) — отдельный `bandit` не нужен. `pip-audit` — supply-chain (CVE в
> зависимостях). Безопасность **CI-workflow** (это тоже атакуемая поверхность) — см. блок CI ниже.

> Батч-гейты CI: `make type`, `make sec`. В сессии их дополняют `pyright-lsp` (типы по мере правок)
> и `/code-review` + `/security-review` (ревью диффа) — см. DoD в [policy-and-docs.md](policy-and-docs.md).

## Типизатор: `ty` или `mypy` (не хардкодь)

Ландшафт сместился — выбирай по проекту, предварительно проверив, что установлено и проходит:

- **`ty`** (Astral, Rust) — на порядок быстрее, ставится в один ряд с ruff/uv. Но **Beta и без
  системы плагинов** (и не планируется): `django-stubs`, Pydantic-v1, SQLAlchemy-стабы он **не
  питает**. Бери, если нужна скорость и хватает базовой проверки; в CI держи как advisory
  (`continue-on-error`), пока инструмент молодой.
- **`mypy` + стабы** (`django-stubs`, `djangorestframework-stubs`) — медленнее, но даёт точную
  типизацию Django ORM / DRF / SQLAlchemy через плагины. Бери, если важна ORM-точность.
- **Грабли:** если в проекте лежит `django-stubs`, а `make type` гонит `ty` — стабы мёртвый груз
  (питают только mypy/pyright). Согласуй: либо `mypy`, либо убери стабы.
- **Раскладка `apps/` в `sys.path`** (частая в Django): типизатору и pytest надо подсказать путь —
  `[tool.pytest.ini_options] pythonpath = ["apps"]` и `[tool.ty.environment] extra-paths = ["apps"]`,
  иначе короткие импорты (`from blog.models import …`) считаются неразрешёнными и раздувают шум.

## pytest должен реально коллектить (Django)

Тесты часто «есть», но не запускаются. Минимум в `pyproject.toml`:
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["apps"]          # если приложения в sys.path
python_files = ["test_*.py", "tests.py"]
```
В Фазе 4 убедись, что `pytest --collect-only` собирает тесты, а не падает на импортах.

## Цели под класс проекта

Добавляй к базе только то, что соответствует проекту.

### Django (веб)
```makefile
migrations-check: ; $(RUN) python manage.py makemigrations --check --dry-run  # CI: упасть, если миграция забыта
check:            ; $(RUN) python manage.py check --deploy                    # deploy-проверки
migrate:          ; $(RUN) python manage.py migrate
run:              ; $(RUN) python manage.py runserver
# test переопредели на pytest -q (с pytest-django) или python manage.py test
```
Перед `migrate` на проде — навык `migration-safety-auditor`.

### FastAPI (API)
```makefile
run:      ; $(RUN) uvicorn app.main:app --reload
migrate:  ; $(RUN) alembic upgrade head
revision: ; $(RUN) alembic revision --autogenerate -m "$(m)"   # autogenerate ВСЕГДА ревьюить
```

### aiogram (бот)
Бота нет смысла «сёрвить» как HTTP — это polling-воркер. Цель запуска и юнит для деплоя:
```makefile
run-bot: ; $(RUN) python -m bot
```
Тесты — на хендлеры/FSM (pytest + aiogram test utils), линт/тип/sec — те же. У бота свой
жизненный цикл: graceful shutdown, idempotent-обработка апдейтов, RedisStorage для FSM.

### Automation-скрипт
Часто без «run»-сервиса: достаточно `lint/type/test/sec` + цель запуска самого скрипта и
заметка про cron/systemd-timer.

## CI — GitHub Actions

Джобы под сам код, без образов, если проект не собирает контейнер. **Не гоняй один `make all` на
голом runner** — `test`/`sec` для
Django/FastAPI требуют БД/Redis и упадут. Дроби джобы **по capability**: чистые проверки отдельно,
сервис-зависимые отдельно.

```yaml
name: ci
on:
  # Safe-by-default: пока не настроены секреты/доступы — только ручной запуск.
  # Включить авто-CI: раскомментировать push/pull_request.
  workflow_dispatch:
  # push: { branches: [main, master] }
  # pull_request: { branches: [main, master] }
jobs:
  lint:                                   # без сервисов
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6       # пинуй сторонние actions по SHA (zizmor: unpinned-uses)
      - run: uv sync --all-groups
      - run: make lint fmt-check
      - run: make type                    # ty молодой → можно continue-on-error
        continue-on-error: true
  test:                                   # с сервисами (пример для Django)
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16, env: { POSTGRES_PASSWORD: x }, ports: ['5432:5432'],
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5 }
      redis: { image: redis:7, ports: ['6379:6379'] }
    env: { SECRET_KEY: ci-not-secret, DB_HOST: localhost, DB_PASSWORD: x, REDIS_CACHE_URL: redis://localhost:6379/2 }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --all-groups
      - run: make migrations-check        # упасть, если миграция забыта
      - run: make test
  sec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --all-groups
      - run: make sec
```

- **Тестовая джоба использует dummy-секреты** (заданы в `env:`/сервисах), реальные GitHub Secrets
  для `lint/test/sec` не нужны — они понадобятся только джобе деплоя.
- **CI-workflow — атакуемая поверхность.** Пинуй сторонние actions по commit-SHA и прогоняй
  [`zizmor`](https://github.com/zizmorcore/zizmor) (статанализ GitHub Actions: template injection,
  утечки секретов, `unpinned-uses`) — отдельным шагом в `sec` или как `zizmor-action`. Поводы
  реальны: в 2026 через мисконфиг `pull_request_target` в action увели секреты и бэкдорнули пакет.
- FastAPI с Alembic — в `test`-джобе шаг `make migrate` на тестовой БД.

## Деплой — по фактической модели проекта

Не навязывай модель выкатки: определи её из репозитория (`Dockerfile`/`compose` → контейнеры;
юнит-файлы и конфиг nginx → systemd; `Procfile`/манифест провайдера → PaaS) и делай обвязку под
неё. Если следов нет — спроси, а не подставляй умолчание.

Для деплоя на одиночный сервер без контейнеров типовая связка: gunicorn/uvicorn (или бот-воркер)
под systemd за nginx, redis как broker/cache/FSM-storage, postgres. Деплой-заметку в репозитории
держи короткой (юнит-файл, `systemctl restart`, где конфиг nginx). Подробный деплой-навык — отдельно.
