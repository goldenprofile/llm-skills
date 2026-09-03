# Tooling — задачи-команды и CI под Python-стек

Стек известен: Python (Django / FastAPI / aiogram). Многостековые таблицы не нужны.
Инструменты по умолчанию: **ruff** (lint + format + security-правила `S`, нативная замена bandit),
**pytest** (+ pytest-django / httpx для FastAPI), **pip-audit** (supply-chain). Типизатор — **по
проекту, не хардкодь** (см. «Типизатор» ниже): `ty` (быстрый, без плагинов) или `mypy`+стабы.
Сначала **детектни, что реально установлено и проходит**, и подстрой цели под это.

## Runner: канонический command contract

Контракт — это **имена целей**, а не конкретный раннер: `make lint`, `just lint` и `nox -s lint`
запускают одно и то же. Имена ниже обязательны; чем они запускаются — свойство проекта.

Раннер выбирай, а не подставляй по умолчанию:

1. **Он уже есть** (`Makefile`, `justfile`, `noxfile.py`, `[tool.poe]`, npm-scripts) — бери его
   и приводи имена целей к канону. Второй раннер рядом с первым заводить нельзя.
2. **Ничего нет** — `Makefile` как умолчание: читаем, без зависимостей, одинаков в CI. Но
   **`make` не входит в штатную поставку Windows**: если на проекте есть Windows-машины,
   либо запиши установку предусловием в policy (Git for Windows, chocolatey, scoop, WSL),
   либо возьми `just` — один бинарь, теми же именами целей, ставится в том числе через
   `uv tool install rust-just`.
3. **В CI** раннер ставится явным шагом, поэтому там вопроса нет.

Сам `Makefile` как файл переносим; непереносимо **наличие `make` в PATH**. Не пиши в policy
«make кросс-платформенный» — проверь, что требуется на самом деле, и запиши это.

## Канонический namespace целей — обязателен для всех проектов

Один и тот же агент работает в ~16 репозиториях. Если `make check` в каждом значит своё,
DoD «`make check` зелёный» — не контракт, а пожелание. Имена ниже обязательны; проектная
специфика добавляется, но **не переименовывает** канон.

**Атомарные цели — одна цель, один инструмент:**

| Цель | Что делает | Меняет файлы |
|------|-----------|--------------|
| `lint` | статический анализ (ruff check) | нет |
| `format` | форматирование (ruff format) | **да** |
| `format-check` | то же, только проверка | нет |
| `type` | типы (mypy/pyright/ty) | нет |
| `test` | тесты | нет |
| `sec` | секьюрити-сканы (ruff S, pip-audit, gitleaks) | нет |
| `migrations-check` | Django: нет несозданных миграций | нет |

**Агрегаты — их ровно два:**

- `check` — **единственный блокирующий гейт**. Обязательный минимум:
  `lint format-check type test` (+ `migrations-check` в Django). Сверху — проектные
  добавки (шаблоны, ассеты, css) и `sec`. Жёсткий инвариант ровно один:
  **`check` никогда не меняет файлы** — ради этого `format-check` и существует отдельно
  от `format`. Это то, на что ссылается DoD и что форсит pre-push.
- `sec` — существует отдельной целью **всегда**, даже когда включён в `check`:
  перед релизом его гоняют прицельно.

Сеть и сервисы — не инвариант, а свойство проекта: `sec` (pip-audit) ходит в сеть,
в xpx.ru тестам нужны PostgreSQL и Redis. Держать `check` запускаемым на десктопе
желательно (тесты на in-memory SQLite — так в nameregister и digital-goods-store).
Где невозможно, гейт гоняется в CI, а в CLAUDE.md проекта прямо написано, какое
подмножество бежит локально. Разное **имя** гейта под разное окружение запрещено:
именно так namespace и расползается.

Цель, которую в проекте сознательно сделали advisory (в xpx.ru `ty` стоит в CI
с `continue-on-error`), в `check` не входит — иначе гейт красный по умолчанию,
и его начинают обходить. Она остаётся отдельной целью, и причина пишется рядом.

**Запрещено:** `all`, `verify`, `preflight`, `check-all` как *разные* гейты. Один проект —
один блокирующий гейт с именем `check`. Старые имена оставлять только алиасами:
`fmt`→`format`, `fmt-check`→`format-check`, `typecheck`→`type`, `all`→`check`.

**Почему `check`, а не `all`:** по конвенции GNU `all` — «собрать», `check` — «проверить».
У Python-проектов собирать нечего, поэтому `all` как имя гейта вводит в заблуждение.

**Правило для DoD:** пункт DoD, для которого существует цель Makefile, в DoD не пишется —
он уже внутри `check`. Проза в чек-листе остаётся только для того, что машина проверить
не может (покрыт ли сценарий отказа, синхронизирован ли backlog, уместно ли решение).

### `Makefile` (база, общая для всех Python-проектов)

```makefile
# подставь свой менеджер пакетов: uv run / poetry run / python -m
RUN := uv run

.PHONY: lint format format-check fix type test sec migrations-check check
lint:         ; $(RUN) ruff check .
format:       ; $(RUN) ruff format .              # ТОЛЬКО формат — без --fix (см. ниже)
format-check: ; $(RUN) ruff format --check .      # CI: упасть, если не отформатировано
fix:          ; $(RUN) ruff check --fix .         # автофикс ОТДЕЛЬНО и осознанно (см. ниже)
type:         ; $(RUN) ty check                   # ИЛИ mypy . — выбор типизатора см. ниже
test:         ; $(RUN) pytest -q
sec:          ; $(RUN) ruff check --select S . && $(RUN) pip-audit
check: lint format-check type test   # единственный блокирующий гейт; файлы НЕ меняет
#         + migrations-check (Django), + sec — проектные добавки поверх минимума
```

> **Почему `format` без `--fix`.** `ruff check --fix` сносит «неиспользуемые» импорты (F401). В Django
> такой импорт часто регистрирует сигналы/админку (side-effect) — слепой автофикс ломает регистрацию.
> Держи формат (`format`) и автофикс (`fix`) **раздельно**, F401 на Django-коде ревьюь руками.

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

Джобы под сам код, без образов, если проект не собирает контейнер. **Не гоняй один `make check` на
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
      - run: make lint format-check
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
