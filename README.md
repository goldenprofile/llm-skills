# LLM Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/format-SKILL.md-success.svg)](#формат-навыка)
[![Skills: 26](https://img.shields.io/badge/skills-26-informational.svg)](#каталог-навыков)

Коллекция переиспользуемых **агентских навыков** (Agent Skills) для LLM-ассистентов
программирования — прежде всего [Claude Code](https://docs.claude.com/en/docs/claude-code),
а также [OpenCode](https://opencode.ai). Каждый навык — это самодостаточная инструкция в
формате `SKILL.md`, которую ассистент загружает по требованию, когда задача соответствует
описанию навыка.

Навыки сфокусированы на повседневной разработке: аудит и отладка Django/Python-проектов,
технический SEO, анализ незнакомых кодовых баз, code review, организация работы агента,
ведение заметок (Obsidian) и проверка фактов.

---

## Содержание

- [Что такое навык](#что-такое-навык)
- [Совместимость](#совместимость)
- [Установка](#установка)
- [Каталог навыков](#каталог-навыков)
- [Формат навыка](#формат-навыка)
- [Структура репозитория](#структура-репозитория)
- [Создание нового навыка](#создание-нового-навыка)
- [Лицензия](#лицензия)

---

## Что такое навык

Навык (skill) — это папка с файлом `SKILL.md`, который содержит:

- **YAML-фронтматтер** с полями `name` и `description` — по описанию ассистент решает,
  когда навык применим;
- **тело инструкции** — пошаговый процесс, чек-листы и правила, которым следует агент;
- опциональную папку **`references/`** с дополнительными материалами (шаблоны отчётов,
  чек-листы, примеры), которые подгружаются только при необходимости —
  принцип *progressive disclosure*.

Такой формат позволяет держать основную инструкцию компактной, а тяжёлые детали выносить
в отдельные файлы, экономя контекст модели.

---

## Совместимость

| Инструмент | Поддержка | Каталог навыков |
|------------|-----------|-----------------|
| **Claude Code** | нативная | `~/.claude/skills/` (глобально) или `.claude/skills/` (в проекте) |
| **OpenCode** | нативная, в т.ч. чтение Claude-совместимых путей | `~/.config/opencode/skills/`, `.opencode/skills/`, а также `~/.claude/skills/` и `.claude/skills/` |

> OpenCode умеет читать навыки напрямую из каталогов Claude Code, поэтому одна установка
> в `~/.claude/skills/` делает навыки доступными сразу в обоих инструментах.

Формат `SKILL.md` совместим с экосистемой Anthropic Agent Skills, поэтому навыки можно
использовать и в других средах, поддерживающих этот стандарт.

---

## Установка

### Вариант 1. Клонировать всё и связать с каталогом навыков

```bash
git clone https://github.com/goldenprofile/skills.git llm-skills
cd llm-skills
```

Скопируйте нужные навыки в каталог вашего инструмента. Например, глобально для Claude Code
(и автоматически для OpenCode):

```bash
# Linux / macOS
mkdir -p ~/.claude/skills
cp -r 500-error-eliminator django-audit techlead-ai ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse 500-error-eliminator, django-audit, techlead-ai "$HOME\.claude\skills\"
```

### Вариант 2. Установить отдельный навык

Скопируйте одну папку навыка целиком (вместе с её `references/`, если есть) в каталог
навыков. Имя папки должно совпадать с полем `name` во фронтматтере.

### Вариант 3. Навыки уровня проекта

Поместите папки навыков в `.claude/skills/` внутри репозитория проекта — тогда они будут
доступны всем, кто работает с этим проектом через Claude Code или OpenCode.

После установки навык активируется автоматически, когда ваш запрос соответствует его
описанию. В Claude Code список доступных навыков можно посмотреть, упомянув их по имени.

---

## Каталог навыков

### Django

| Навык | Назначение |
|-------|------------|
| [`500-error-eliminator`](500-error-eliminator/) | Систематическая диагностика и устранение Django 500 Internal Server Error: код, конфигурация, шаблоны, логи. |
| [`advanced-seo-optimizer`](advanced-seo-optimizer/) | Глубокий технический SEO-аудит Django: семантика, meta/OG, Schema.org JSON-LD, robots/sitemap, hreflang, Core Web Vitals. |
| [`django-audit`](django-audit/) | Комплексный аудит Django по линзам: архитектура, безопасность (OWASP), Celery, чистота кода, техдолг, готовность к деплою, тесты. |
| [`django-tailwind-optimizer`](django-tailwind-optimizer/) | Анализ Django-шаблонов на Tailwind CSS: дублирование стилей, переход с CDN на production-сборку. |

### FastAPI

| Навык | Назначение |
|-------|------------|
| [`fastapi-architect`](fastapi-architect/) | Проектирование и ревью FastAPI: структура (APIRouter, lifespan, pydantic-settings), Pydantic v2, async-корректность (блокировка event loop, SQLAlchemy 2.x async), DI, тесты (httpx + dependency_overrides). |

### База данных и миграции

| Навык | Назначение |
|-------|------------|
| [`migration-safety-auditor`](migration-safety-auditor/) | Аудит безопасности миграций БД (Django + Alembic) перед прод-деплоем: блокировки таблиц, downtime, потеря данных, обратная совместимость при zero-downtime, опасный backfill. Postgres и SQLite. |

### Python и качество кода

| Навык | Назначение |
|-------|------------|
| [`python-project-audit`](python-project-audit/) | «Проверка на блуд»: аудит бэкенда (FastAPI/Django/Flask) на готовность к продакшену — статанализ и ручной review с отчётом. |
| [`test-coverage-auditor`](test-coverage-auditor/) | Аудит качества тестов Python/Django: тесты без assertions, моки без проверок, непокрытый критический код, skip без причины. |
| [`techlead-ai`](techlead-ai/) | Строгое, но конструктивное code review уровня Senior Architect: баги, OWASP Top 10, производительность, Clean Code, SOLID. |
| [`claude-code-auditor`](claude-code-auditor/) | «Второе мнение» на код, написанный Claude Code, силами **другой** LLM (DeepSeek/GLM/Kimi) через CLI Hermes (`hermes -z`): галлюцинации API, edge cases, over-engineering, отклонения от паттернов. Пять линз (Скептик, Безопасность, Надёжность, Производительность, Поддерживаемость). Требует установленного CLI `hermes`. |
| [`dependency-auditor`](dependency-auditor/) | Аудит зависимостей и supply-chain Python: pip-audit/safety и CVE, пиннинг и lockfiles (uv/poetry/pip-tools), безопасные апгрейды с разбором breaking changes. |

### Telegram-боты (aiogram)

| Навык | Назначение |
|-------|------------|
| [`aiogram-bot-auditor`](aiogram-bot-auditor/) | Аудит и помощь по ботам на aiogram 3.x: надёжность Telegram API (flood-control 429, блокировки, single instance), архитектура (Router/middlewares/FSM), деплой (polling под systemd, webhook+nginx, RedisStorage) и тесты. |

### Деплой и инфраструктура

| Навык | Назначение |
|-------|------------|
| [`vps-deploy-auditor`](vps-deploy-auditor/) | Деплой Python-приложений на VPS без Docker: nginx + systemd + redis + postgres. Генерация конфигов и аудит существующего деплоя (Django/FastAPI/боты) с уровнями риска. |

### Анализ кодовой базы

| Навык | Назначение |
|-------|------------|
| [`code-archaeologist`](code-archaeologist/) | Быстрое восстановление архитектуры незнакомого проекта: стек, точки входа, потоки данных, бизнес-цели. |
| [`codebase-express`](codebase-express/) | Целевой экспресс-анализ конкретного аспекта кодовой базы с gap-анализом «текущее против желаемого». |

### Рабочий процесс агента

| Навык | Назначение |
|-------|------------|
| [`agent-audit`](agent-audit/) | Самоаудит AI-агента: актуальность проектной документации, повторяющиеся ошибки, генерация guardrails. |
| [`clarify-prompt`](clarify-prompt/) | Превращение нечётких разговорных задач в структурированные однозначные промты для AI-агента. |
| [`git-commit-planner`](git-commit-planner/) | Разбор изменений в git и план логических атомарных коммитов вместо одного монолитного. |
| [`session-catchup`](session-catchup/) | Возобновление прерванной сессии: восстановление контекста из git, файлов состояния и истории диалога. |
| [`harness-engineering`](harness-engineering/) | Обвязка Python-проекта для AI-агентов: Makefile, CI (GitHub Actions), `ARCHITECTURE.md`, синхронизация `CLAUDE.md`/`AGENTS.md`, а Definition of Done вызывает остальные навыки библиотеки. Деплой systemd/nginx, Symphony опционально. |

### Документация

| Навык | Назначение |
|-------|------------|
| [`docs-generator`](docs-generator/) | Документация для соло: README, ADR, docstrings (Google style) и синхронизация `CLAUDE.md`/`AGENTS.md`. Генерация недостающего и аудит устаревшего. |
| [`spec-writer`](spec-writer/) | Проектные документы в трёх режимах: spec (техспецификация: проблема, цели, архитектура, ADR-решения, риски), plan (фазы, оценки, зависимости) и brief (аналитическая записка для руководства, без кода). Создан совместно с Hermes Agent. |

### Заметки и знания

| Навык | Назначение |
|-------|------------|
| [`obsidian`](obsidian/) | Работа с хранилищем Obsidian (filesystem-first): клиппинги, проектные задачи со статусами, ADR, дневник, бриф проекта, синтез исследований, ревью и анализ графа тегов/ссылок. Создан совместно с Hermes Agent. |

### Окружение разработки

| Навык | Назначение |
|-------|------------|
| [`windows-pwsh-terminal`](windows-pwsh-terminal/) | Диагностика и модернизация терминала на Windows: WezTerm + PowerShell 7 + scoop. Методика с чеклистом, развилками и типовыми граблями (starship/atuin/fzf/zoxide), read-only скрипт диагностики. |

### SEO и контент

| Навык | Назначение |
|-------|------------|
| [`google-discover-optimize`](google-discover-optimize/) | Аудит и оптимизация статей под Google Discover: изображения, E-E-A-T, NewsArticle JSON-LD, мобильные Core Web Vitals. |

### Исследование и факты

| Навык | Назначение |
|-------|------------|
| [`fact-checker`](fact-checker/) | Систематическая проверка фактов и выявление дезинформации с обязательной верификацией источников через веб-поиск. |

---

## Формат навыка

```
<имя-навыка>/
├── SKILL.md            # обязательный: фронтматтер + инструкция
└── references/         # опционально: подгружаемые по требованию материалы
    ├── checklist.md
    └── template.md
```

Минимальный `SKILL.md`:

```markdown
---
name: my-skill
description: >
  Кратко — что делает навык и КОГДА его применять. Описание используется
  ассистентом для срабатывания, поэтому формулируйте триггеры явно
  («используй когда пользователь просит …»). Минимум ~20 символов.
---

# My Skill

Пошаговая инструкция, которой следует агент…
```

Требования к фронтматтеру:

- `name` должен совпадать с именем папки навыка;
- `description` должен содержательно описывать назначение **и условия срабатывания**.

---

## Структура репозитория

```
.
├── 500-error-eliminator/
├── advanced-seo-optimizer/
├── agent-audit/
├── aiogram-bot-auditor/
├── clarify-prompt/
├── claude-code-auditor/
├── code-archaeologist/
├── codebase-express/
├── dependency-auditor/
├── django-audit/
├── django-tailwind-optimizer/
├── docs-generator/
├── fact-checker/
├── fastapi-architect/
├── git-commit-planner/
├── google-discover-optimize/
├── harness-engineering/
├── migration-safety-auditor/
├── obsidian/
├── python-project-audit/
├── session-catchup/
├── spec-writer/
├── techlead-ai/
├── test-coverage-auditor/
├── vps-deploy-auditor/
├── windows-pwsh-terminal/
├── .gitattributes      # нормализация переводов строк (LF)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Создание нового навыка

1. Создайте папку с именем навыка в kebab-case.
2. Добавьте `SKILL.md` с фронтматтером (`name` = имя папки) и инструкцией.
3. Вынесите объёмные материалы в `references/` и ссылайтесь на них из `SKILL.md`.
4. Сформулируйте `description` так, чтобы ассистент понимал, **когда** применять навык.
5. Проверьте навык на реальной задаче перед коммитом.

Описания навыков в этом репозитории написаны на русском языке, что задаёт язык
взаимодействия по умолчанию; сами навыки работают с задачами на любом языке.

---

## Лицензия

Распространяется по лицензии [MIT](LICENSE). © 2026 Ivan Sinyavskiy.
