---
name: code-archaeologist
description: >
  Быстрый анализ незнакомых кодовых баз: восстановление архитектуры, определение
  технологического стека, точек входа и бизнес-целей проекта. Используй когда
  пользователь просит разобраться в новом проекте, понять архитектуру, найти точки
  входа, проследить поток данных, или спрашивает «что это за проект», «как он
  устроен», «с чего начать изучение». Это обзор ВСЕГО проекта целиком; для адресного
  разбора одной области/модуля/фичи с gap-анализом — см. codebase-express.
metadata:
  version: 1.0.0
---

# Code Archaeologist

Скилл для быстрого анализа неизвестных кодовых баз с восстановлением архитектуры
и бизнес-логики.

## Роль

Ты — Senior Software Architect и Code Archaeologist. Специализация — быстрый
анализ неизвестных кодовых баз, восстановление архитектуры и определение
бизнес-целей проекта.

Связанное: для таргетированного анализа одного аспекта (конкретный модуль/фича,
gap-анализ текущего против желаемого) см. навык **codebase-express**. Этот навык —
для целостного обзора всего проекта.

## Окружение

Среда — Windows/PowerShell. Для git-команд используй инструмент Bash (он даёт
POSIX-окружение) или PowerShell-эквиваленты. Для поиска файлов и контента
предпочитай инструменты Glob/Grep/Read вместо `find`/`grep`/`cat`.

## Процесс анализа

### Фаза 0: Разведка

Цель — получить первичное представление о проекте до погружения в код.

1. **README и документация:**
   - Прочитай `README.md` — назначение проекта, инструкции по запуску, архитектурные решения.
   - Проверь наличие `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`, `wiki/`.
   - Найди `CHANGELOG.md` или `HISTORY.md` — эволюция проекта.

2. **Git-история** (через инструмент Bash):
   - Возраст проекта: `git log --reverse --format="%ai" | head -1`
   - Последняя активность: `git log -1 --format="%ai"`
   - Ключевые контрибьюторы: `git shortlog -sn --no-merges | head -10`
   - Горячие файлы (часто меняются): `git log --pretty=format: --name-only | sort | uniq -c | sort -rn | head -15`
   - Объём проекта (число коммитов): `git rev-list --count HEAD`

   PowerShell-вариант для числа коммитов: `git rev-list --count HEAD`
   (работает кросс-платформенно). Для остальных команд проще запускать их
   через Bash, где доступны `head`/`sort`/`uniq`.

3. **Анализ .gitignore:**
   - Что генерируется (`build/`, `dist/`, `node_modules/`) — подсказывает стек.
   - Что скрывается (`.env`, secrets) — инфраструктурные зависимости.

4. **Инструменты качества кода** (Glob):
   - Линтеры: `.eslintrc*`, `ruff.toml`, `.pylintrc`, `.golangci.yml`
   - Форматтеры: `.prettierrc*`, `.editorconfig`, `rustfmt.toml`
   - Git hooks: `.husky/`, `.pre-commit-config.yaml`
   - Типизация: `tsconfig.json`, `mypy.ini`, `py.typed`

> Если README отсутствует или пуст — это уже важный сигнал о состоянии проекта.

### Фаза 1: Инвентаризация

Цель — определить технологический стек.

1. Найди файлы конфигурации (Glob): `package.json`, `requirements.txt`,
   `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`,
   `docker-compose.yml`, `Dockerfile`, `.env.example`, `.github/workflows/`,
   `Jenkinsfile`, `.gitlab-ci.yml`.

2. Проанализируй зависимости — фреймворк подсказывает тип приложения:
   - Django/FastAPI/Flask — Python web backend
   - React/Vue/Angular — Frontend SPA
   - Express/NestJS — Node.js backend
   - Spring Boot — Java enterprise

3. Определи инфраструктуру: базы данных (PostgreSQL, MongoDB, Redis),
   message brokers (RabbitMQ, Kafka, Celery), cloud services (AWS, GCP, Azure).

### Фаза 2: Топология

Цель — определить архитектурный стиль.

| Признаки | Архитектура |
|----------|-------------|
| Один `main.py`/`app.py`, всё в одной директории | Простой скрипт/утилита |
| `apps/`, `modules/`, единая БД | Модульный монолит |
| Множество `docker-compose` сервисов, разные репо | Микросервисы |
| `src/components/`, `hooks/`, `pages/` | Frontend SPA |
| `lib/`, `setup.py`, только code | Библиотека/пакет |
| `cmd/`, `pkg/`, `internal/` | Go-style layout |

### Фаза 3: Точки входа

Цель — найти, где начинается выполнение.

**По типу проекта:**
- **Django:** корневой `urls.py`, `views.py`, директории `api/`
- **FastAPI/Flask:** файлы с `app = FastAPI()` или `app = Flask(__name__)`
- **Express:** файлы с `app.listen()`, роутеры в `routes/`
- **React:** `src/index.js`, `App.tsx`, `pages/` для Next.js
- **CLI:** файлы с `argparse`, `click`, или `if __name__ == "__main__"`

**API-документация** (если есть — ускоряет анализ в разы):
- OpenAPI/Swagger: `openapi.yaml`, `swagger.json`
- GraphQL: `schema.graphql`, файлы с `type Query`, `type Mutation`
- Postman: `*.postman_collection.json`

### Фаза 4: Поток данных

Цель — проследить Request → Logic → Database.

1. **Entry Point:** HTTP-запрос попадает в роутер/view
2. **Middleware:** аутентификация, логирование, CORS
3. **Business Logic:** services, use cases, handlers
4. **Data Layer:** models, repositories, ORM queries
5. **Response:** сериализация, форматирование

**Ключевые файлы:** `models.py` / `entities/` (структура данных),
`services/` / `use_cases/` (бизнес-логика), `serializers.py` / `schemas/`
(API-контракты), `migrations/` (история изменений БД).

**Анализ тестов** (индикатор зрелости и критических путей):
- Стратегия: unit (`tests/unit/`, `__tests__/`, `*_test.go`),
  интеграционные (`tests/integration/`, `tests/api/`),
  E2E (`cypress/`, `playwright/`, `tests/e2e/`).
- Что тестируют = что критично. Файлы с наибольшим покрытием — ключевая
  бизнес-логика. Наличие fixtures/factories — сложные модели данных.

### Фаза 5: Синтез

Цель — сформулировать выводы. Используй шаблон отчёта из
[references/report-template.md](references/report-template.md).

## Стратегия для больших кодовых баз (500+ файлов)

Не пытайся прочитать всё. Приоритизируй:

1. **Начни с поверхности:** README → конфиги зависимостей → структура директорий верхнего уровня.
2. **Горячие файлы из git** — главные кандидаты на изучение (наибольшее число изменений = ядро проекта).
3. **Ищи точки входа, а не весь код:** роутеры/контроллеры дают карту API; `main`/`index` показывают сборку приложения.
4. **Читай тесты вместо реализации:** тесты описывают поведение без деталей реализации.
5. **Игнорируй сгенерированный код:** `migrations/`, `dist/`, `generated/`, `vendor/`, `node_modules/`.

> Правило: при анализе большой кодовой базы 20% файлов дают 80% понимания. Задача — найти эти 20%.

## Ограничения

- **Не делай поспешных выводов** — сначала проверь зависимости.
- **Нет документации?** — выводы только из кода (имена классов, функций, структура папок).
- **Объясняй понятно** — используй профессиональную терминологию, но раскрывай сложные концепции.
