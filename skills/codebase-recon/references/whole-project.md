# Режим whole — незнакомый проект целиком

Цель — восстановить архитектуру, стек и бизнес-цель проекта настолько, чтобы
можно было осмысленно принимать решения о работе с ним.

## Фаза 0. Разведка

Первичное представление до погружения в код.

1. **README и документация**
   - `README.md` — назначение, запуск, архитектурные решения.
   - Проверь `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`, `wiki/`.
   - `CHANGELOG.md` / `HISTORY.md` — эволюция проекта.
2. **Git-история** (через инструмент Bash)
   - Возраст: `git log --reverse --format="%ai" | head -1`
   - Последняя активность: `git log -1 --format="%ai"`
   - Ключевые контрибьюторы: `git shortlog -sn --no-merges | head -10`
   - Горячие файлы: `git log --pretty=format: --name-only | sort | uniq -c | sort -rn | head -15`
   - Объём: `git rev-list --count HEAD`
3. **`.gitignore`**
   - Что генерируется (`build/`, `dist/`, `node_modules/`) — подсказывает стек.
   - Что скрывается (`.env`, секреты) — инфраструктурные зависимости.
4. **Инструменты качества** (Glob)
   - Линтеры: `.eslintrc*`, `ruff.toml`, `.pylintrc`, `.golangci.yml`
   - Форматтеры: `.prettierrc*`, `.editorconfig`, `rustfmt.toml`
   - Хуки: `.husky/`, `.pre-commit-config.yaml`
   - Типизация: `tsconfig.json`, `mypy.ini`, `py.typed`

> Отсутствующий или пустой README — уже важный сигнал о состоянии проекта.

## Фаза 1. Инвентаризация

Определить технологический стек.

1. Конфиги зависимостей (Glob): `package.json`, `requirements.txt`,
   `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`,
   `docker-compose.yml`, `Dockerfile`, `.env.example`, `.github/workflows/`,
   `Jenkinsfile`, `.gitlab-ci.yml`.
2. Фреймворк подсказывает тип приложения: Django/FastAPI/Flask — Python-бэкенд;
   React/Vue/Angular — frontend SPA; Express/NestJS — Node-бэкенд;
   Spring Boot — Java enterprise.
3. Инфраструктура: БД (PostgreSQL, MongoDB, Redis), брокеры (RabbitMQ, Kafka,
   Celery), облака (AWS, GCP, Azure).

## Фаза 2. Топология

| Признаки | Архитектура |
|----------|-------------|
| Один `main.py`/`app.py`, всё в одной директории | Простой скрипт/утилита |
| `apps/`, `modules/`, единая БД | Модульный монолит |
| Множество `docker-compose` сервисов, разные репо | Микросервисы |
| `src/components/`, `hooks/`, `pages/` | Frontend SPA |
| `lib/`, `setup.py`, только код | Библиотека/пакет |
| `cmd/`, `pkg/`, `internal/` | Go-style layout |

## Фаза 3. Точки входа

**По типу проекта:**
- **Django:** корневой `urls.py`, `views.py`, директории `api/`
- **FastAPI/Flask:** файлы с `app = FastAPI()` или `app = Flask(__name__)`
- **Express:** файлы с `app.listen()`, роутеры в `routes/`
- **React:** `src/index.js`, `App.tsx`, `pages/` для Next.js
- **CLI:** `argparse`, `click`, `if __name__ == "__main__"`

**API-документация** (если есть — ускоряет анализ в разы):
OpenAPI/Swagger (`openapi.yaml`, `swagger.json`), GraphQL (`schema.graphql`,
`type Query`, `type Mutation`), Postman (`*.postman_collection.json`).

## Фаза 4. Поток данных

Проследить Request → Logic → Database:

1. **Entry point** — HTTP-запрос попадает в роутер/view
2. **Middleware** — аутентификация, логирование, CORS
3. **Business logic** — services, use cases, handlers
4. **Data layer** — models, repositories, ORM-запросы
5. **Response** — сериализация, форматирование

**Ключевые файлы:** `models.py` / `entities/` (структура данных),
`services/` / `use_cases/` (бизнес-логика), `serializers.py` / `schemas/`
(API-контракты), `migrations/` (история изменений схемы).

**Анализ тестов** — индикатор зрелости и критических путей:
- Стратегия: unit (`tests/unit/`, `__tests__/`, `*_test.go`), интеграционные
  (`tests/integration/`, `tests/api/`), E2E (`cypress/`, `playwright/`, `tests/e2e/`).
- Что тестируют — то и критично. Наличие fixtures/factories говорит о сложных
  моделях данных.

## Фаза 5. Синтез

Сформулируй выводы по шаблону [whole-report.md](whole-report.md): назначение
проекта, стек, архитектурный стиль, точки входа, поток данных, состояние
(зрелость, техдолг, риски), с чего начинать работу.
