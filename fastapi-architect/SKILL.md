---
name: fastapi-architect
description: >
  Проектирование и ревью FastAPI-приложений (Pydantic v2): структура проекта
  (APIRouter, lifespan, pydantic-settings, сервисный слой), dependency
  injection, модели vs схемы, async-корректность (блокировка event loop,
  SQLAlchemy 2.x async, def vs async def, BackgroundTasks vs очередь), формат
  ошибок, OpenAPI, тесты (httpx AsyncClient, dependency_overrides). Используй
  когда пользователь проектирует или ревьюит FastAPI-приложение, спрашивает
  «правильно ли устроен мой FastAPI», «почему ручка тормозит/блокирует», «как
  структурировать/тестировать FastAPI», пишет роутеры, зависимости или
  Pydantic-схемы, или упоминает FastAPI, Depends, response_model, lifespan,
  pydantic-settings. Только FastAPI.
metadata:
  version: 1.1.0
---

# FastAPI Architect

Помощник по проектированию и аудиту приложений на **FastAPI** (актуальные версии, **Pydantic v2**).
Два режима: (1) помощь в проектировании нового — структура, схемы, DI, async, тесты; (2) аудит
существующего кода — поймать то, из-за чего ручка блокирует event loop, схема течёт наружу, DI
сделан через глобальные синглтоны, ошибки неконсистентны, а тесты не изолированы. По итогу аудита —
отчёт с уровнями риска и (по согласованию) правки.

## Когда применять

При старте нового сервиса (выбор структуры), при ревью PR с роутами/схемами/зависимостями, при
жалобах «ручка тормозит / весь сервис висит / падает под нагрузкой», при переезде Pydantic v1→v2,
при подключении async-БД, при написании тестов. Только FastAPI. Для Alembic/миграций БД — навык
`migration-safety-auditor`, не дублируй его здесь.

## Контекст — установить ПЕРВЫМ делом

1. **Версии**: FastAPI (актуальная), **Pydantic v1 или v2** (критично — API валидаторов и config
   разный). Признаки v2: `model_config = ConfigDict(...)`, `field_validator`, `model_dump()`.
2. **БД и драйвер**: sync (psycopg2 / sync SQLAlchemy) или async (SQLAlchemy 2.x async + asyncpg).
   От этого зависит, чем должны быть роуты — `async def` или `def`. У владельца — postgres.
3. **Стиль роутов**: всё в одном файле или `APIRouter` по доменам; есть ли сервисный слой.
4. **Запуск**: uvicorn под systemd (профиль владельца), workers, за nginx. Redis для кэша/очередей.
5. **Тесты**: есть ли вообще, используется ли `dependency_overrides` и отдельная тест-БД.

## Процесс

1. Собрать точки входа (`FastAPI(...)`, `lifespan`, `include_router`), роутеры, зависимости
   (`Depends`), Pydantic-схемы, слой БД, обработчики ошибок, тесты, деплой-юнит.
2. Прогнать по чеклисту рисков (ниже) и справочникам.
3. Классифицировать риск, объяснить *почему* ломается именно в проде (под нагрузкой/при async).
4. Предложить безопасную альтернативу с конкретным кодом.
5. Отчёт по [references/output-format.md](references/output-format.md); по согласованию — правки.

## Уровни риска

- **CRITICAL** — сервис недоступен/висит под нагрузкой: блокирующий sync I/O или CPU-работа в
  `async def`-роуте (psycopg2/`requests`/`time.sleep`/тяжёлый расчёт) блокирует весь event loop;
  утечка соединений БД (сессия не закрывается) → пул исчерпан, сервис встаёт.
- **HIGH** — утечка данных или поломка контракта: ORM-модель отдаётся напрямую без `response_model`
  (наружу уходят `password_hash` и пр.); глобальная мутабельная сессия БД на всё приложение
  (data race между запросами); нет обработки исключений → 500 с трейсбеком наружу.
- **MEDIUM** — нет таймаутов на внешние вызовы; DI через глобальные синглтоны вместо `Depends`;
  бизнес-логика в роутах (нетестируемо); смешаны ORM-модели и API-схемы; `BackgroundTasks` для
  тяжёлой/долгой работы вместо внешней очереди; неконсистентный формат ошибок.
- **LOW** — нет тегов/версионирования OpenAPI, именование, мелкие улучшения схем.

## Быстрый чеклист (детали — в справочниках)

- Нет ли блокирующего sync I/O / CPU в `async def`-роуте? (sync-драйвер БД, `requests`,
  `time.sleep`, чтение файла, тяжёлый расчёт → блокируют **весь** event loop). См. `async.md`.
- Роут с sync-БД объявлен как `def` (тогда FastAPI уводит его в threadpool), а не `async def`?
- Сессия БД отдаётся через зависимость с `yield` и закрывается в `finally`? Нет глобальной сессии?
- У каждого роута есть `response_model` (или возвращается схема), а не голая ORM-модель?
- API-схемы (request/response) отделены от ORM-моделей и доменных объектов?
- Pydantic **v2**: `ConfigDict(from_attributes=True)`, `field_validator`/`model_validator`,
  `model_dump`/`model_validate` (не v1-овые `orm_mode`/`@validator`/`.dict()`)? См. `pydantic.md`.
- Зависимости через `Depends`, переопределяемые в тестах через `dependency_overrides`?
- Единый обработчик ошибок и формат (а не россыпь `HTTPException` с разными телами)?
- Внешние вызовы (httpx, БД) с таймаутами? Тяжёлая работа — во внешней очереди, не в `BackgroundTasks`?
- Тесты на `AsyncClient`/`TestClient` с `dependency_overrides` и отдельной тест-БД? См. `testing.md`.

## Связь с библиотекой навыков

- Alembic/миграции схемы перед деплоем → навык **`migration-safety-auditor`** (не дублируется тут).
- Качество и осмысленность тестов (assertion, моки без проверок) → **`test-coverage-auditor`**
  (см. также [references/testing.md](references/testing.md)).
- Ревью диффа предложенных правок → **`techlead-ai`**; полный аудит перед релизом →
  **`python-project-audit`**.

## Справочники

- [references/structure.md](references/structure.md) — структура проекта: APIRouter по доменам,
  `lifespan`, pydantic-settings, тонкие роуты + сервисный слой, сборка приложения.
- [references/pydantic.md](references/pydantic.md) — Pydantic v2: модели vs схемы, `model_config`,
  валидаторы, сериализация, `response_model`, ловушки миграции v1→v2.
- [references/async.md](references/async.md) — async-корректность: блокировка event loop,
  `def` vs `async def` и threadpool, async-БД (SQLAlchemy 2.x), BackgroundTasks, таймауты.
- [references/testing.md](references/testing.md) — pytest + httpx `AsyncClient`/`TestClient`,
  `dependency_overrides`, фикстуры, тест-БД.
- [references/output-format.md](references/output-format.md) — формат отчёта аудита.
