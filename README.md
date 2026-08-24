# LLM Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/format-SKILL.md-success.svg)](#формат-навыка)
[![Skills: 28](https://img.shields.io/badge/skills-28-informational.svg)](#каталог-навыков)

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
| **Другие CLI** (Grok, Codex, Cursor, Hermes, …) | формат [Agent Skills](https://agentskills.io) | каталог навыков инструмента: `~/.grok/skills/`, `~/.agents/skills/`, `~/.cursor/skills/`, `~/.hermes/skills/` (и проектные `.grok/skills/`, `.agents/skills/`, `.cursor/skills/`) |

> OpenCode умеет читать навыки напрямую из каталогов Claude Code, поэтому одна установка
> в `~/.claude/skills/` делает навыки доступными сразу в обоих инструментах.

Формат `SKILL.md` — открытый стандарт Agent Skills: одна папка навыка копируется
в каталог соответствующего CLI без правок содержимого.

---

## Установка

### Вариант 0. Как плагин Claude Code (рекомендуемый)

Репозиторий содержит манифесты плагина (`.claude-plugin/`), поэтому вся
библиотека ставится и обновляется одной парой команд:

```
/plugin marketplace add goldenprofile/llm-skills
/plugin install llm-skills@goldenprofile
```

Обновление после новых релизов: `/plugin marketplace update goldenprofile`.

### Вариант 1. Клонировать всё и связать с каталогом навыков

```bash
git clone https://github.com/goldenprofile/llm-skills.git llm-skills
cd llm-skills
```

Скопируйте нужные навыки в каталог вашего инструмента. Например, глобально для Claude Code
(и автоматически для OpenCode):

```bash
# Linux / macOS
mkdir -p ~/.claude/skills
cp -r skills/django-audit skills/change-review skills/vps-ops ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse skills/django-audit, skills/change-review, skills/vps-ops "$HOME\.claude\skills\"
```

### Вариант 2. Установить отдельный навык

Скопируйте одну папку из `skills/<имя>/` целиком (вместе с её `references/`, если есть) в каталог
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
| [`advanced-seo-optimizer`](skills/advanced-seo-optimizer/) | Глубокий технический SEO-аудит Django и FastAPI (Jinja2): семантика, meta/OG, Schema.org JSON-LD, robots/sitemap, hreflang, Core Web Vitals, AI-краулеры и llms.txt. |
| [`django-audit`](skills/django-audit/) | Комплексный аудит Django по линзам: архитектура, безопасность (OWASP), Celery, чистота кода, техдолг, готовность к деплою, тесты. |
| [`django-tailwind-optimizer`](skills/django-tailwind-optimizer/) | Анализ Django-шаблонов на Tailwind CSS: дублирование стилей, переход с CDN на production-сборку. |

### FastAPI

| Навык | Назначение |
|-------|------------|
| [`fastapi-architect`](skills/fastapi-architect/) | Проектирование и ревью FastAPI: структура (APIRouter, lifespan, pydantic-settings), Pydantic v2, async-корректность (блокировка event loop, SQLAlchemy 2.x async), DI, тесты (httpx + dependency_overrides). |

### База данных и миграции

| Навык | Назначение |
|-------|------------|
| [`migration-safety-auditor`](skills/migration-safety-auditor/) | Аудит безопасности миграций БД (Django + Alembic) перед прод-деплоем: блокировки таблиц, downtime, потеря данных, обратная совместимость при zero-downtime, опасный backfill. Postgres и SQLite. |
| [`postgres-performance`](skills/postgres-performance/) | Диагностика и тюнинг производительности PostgreSQL: EXPLAIN ANALYZE, индексы, pg_stat_statements, pgbouncer, autovacuum, память VPS. |

### Python и качество кода

| Навык | Назначение |
|-------|------------|
| [`python-project-audit`](skills/python-project-audit/) | Проверка заявленной готовности против фактической: незавершённый код, критические проблемы, мёртвые куски. Статанализ (pylint, bandit, mypy, radon, vulture) + ручной review, отчёт с баллами и вердиктом. |
| [`test-writer`](skills/test-writer/) | Написание тестов (pytest-first): стратегия покрытия, дизайн кейсов, фикстуры/фабрики, паттерны Django/FastAPI/aiogram. |
| [`test-coverage-auditor`](skills/test-coverage-auditor/) | Аудит качества тестов Python/Django: тесты без assertions, моки без проверок, непокрытый критический код, skip без причины. |
| [`change-review`](skills/change-review/) | Глубокий разбор ОДНОГО изменения с вердиктом APPROVE / REQUEST CHANGES и шкалой критичности. Режимы: **self** (силами Claude — корректность, безопасность, надёжность, границы слоёв) и **second-opinion** (другая модель через CLI `hermes`: галлюцинации API, edge cases, over-engineering). |
| [`dependency-auditor`](skills/dependency-auditor/) | Аудит зависимостей и supply-chain Python: pip-audit/safety и CVE, пиннинг и lockfiles (uv/poetry/pip-tools), безопасные апгрейды с разбором breaking changes. |

### Telegram-боты (aiogram)

| Навык | Назначение |
|-------|------------|
| [`aiogram-bot-auditor`](skills/aiogram-bot-auditor/) | Аудит и помощь по ботам на aiogram 3.x: надёжность Telegram API (flood-control 429, блокировки, single instance), архитектура (Router/middlewares/FSM), деплой (polling под systemd, webhook+nginx, RedisStorage) и тесты. |

### Деплой и инфраструктура

| Навык | Назначение |
|-------|------------|
| [`vps-ops`](skills/vps-ops/) | Эксплуатация на VPS без Docker (nginx + systemd + postgres + redis) в трёх режимах: **deploy** (конфиги и аудит деплоя), **observe** (Sentry, healthcheck, логи, алерты), **triage** (runbook инцидента: 502/504, рестарт-луп, диск, postgres). |

### Анализ кодовой базы

| Навык | Назначение |
|-------|------------|
| [`codebase-recon`](skills/codebase-recon/) | Разведка кодовой базы в двух режимах: **whole** (незнакомый проект целиком — стек, точки входа, потоки данных, бизнес-цель) и **subject** (одна область или фича адресно, с gap-анализом «текущее против желаемого»). Только чтение. |

### Рабочий процесс агента

| Навык | Назначение |
|-------|------------|
| [`agent-workflow`](skills/agent-workflow/) | Работа с самим агентом в пяти режимах: **delegate** (сам или агент, какой режим и модель), **decompose** (разбить задачу на куски в один заход), **prompt** (из разговорного описания в однозначное задание), **context** (деградация сессии, слои знания, чек-лист CLAUDE.md), **audit** (ретроспектива: повторяющиеся ошибки, протухшая документация, guardrails). |
| [`git-commit-planner`](skills/git-commit-planner/) | Разбор изменений в git и план логических атомарных коммитов вместо одного монолитного. |
| [`release-manager`](skills/release-manager/) | Релизы: semver по диффу, CHANGELOG из Conventional Commits, git-теги и GitHub Releases, пре-релизный чеклист и smoke. |
| [`session-catchup`](skills/session-catchup/) | Возобновление прерванной сессии: восстановление контекста из git, файлов состояния и истории диалога. |
| [`harness-engineering`](skills/harness-engineering/) | Обвязка Python-проекта для AI-агентов: Makefile, CI (GitHub Actions), `ARCHITECTURE.md`, синхронизация `CLAUDE.md`/`AGENTS.md`, а Definition of Done вызывает остальные навыки библиотеки. Деплой systemd/nginx, Symphony опционально. |
| [`goal-pipeline`](skills/goal-pipeline/) | Минимальный планировщик-исполнитель поверх нативной `/goal` Claude Code: лёгкий recon, разбивка brownfield-задачи на фазы с измеримыми критериями, вшитые гейты toolkit по типу фазы (migration-safety-auditor, /code-review, pyright, test-coverage-auditor), одна готовая строка `/goal`, аудит против исходного плана. Профили автономности с чекпоинтом на рискованных фазах. |
| [`ratchet-loop`](skills/ratchet-loop/) | In-session петля-храповик: тянет ОДИН измеримый скаляр (latency, число SQL-запросов, размер бандла, pass-rate) до упора — оставляет только улучшившие изменения, остальное откатывает через git. Замороженный оценщик (anti-Goodhart) + независимый verifier-проход; сама не терминируется, крутится до бюджета/плато. |

### LLM в продукте

| Навык | Назначение |
|-------|------------|
| [`llm-feature-architect`](skills/llm-feature-architect/) | Проектирование и ревью LLM-фич в продукте (Django/FastAPI/aiogram): форма задачи и модель, сервис-обёртка с ретраями и очередью, structured output + pydantic, контроль стоимости, evals на золотом наборе, prompt injection и PII. |

### Документация

| Навык | Назначение |
|-------|------------|
| [`docs-generator`](skills/docs-generator/) | Документация: README, ADR, docstrings (Google style) и синхронизация `CLAUDE.md`/`AGENTS.md`. Генерация недостающего и аудит устаревшего. |
| [`sage`](skills/sage/) | Координатор виртуальной команды: сырой вход (черновик, пост, схема) → пакет документов (summary, discussion, design/runbook). Не один spec. |
| [`spec-writer`](skills/spec-writer/) | Проектные документы в трёх режимах: spec (техспецификация: проблема, цели, архитектура, ADR-решения, риски), plan (фазы, оценки, зависимости) и brief (аналитическая записка для руководства, без кода). |

### Заметки и знания

| Навык | Назначение |
|-------|------------|
| [`obsidian`](skills/obsidian/) | Работа с хранилищем Obsidian (filesystem-first): клиппинги, проектные задачи со статусами, ADR, дневник, бриф проекта, синтез исследований, ревью и анализ графа тегов/ссылок. |

### SEO и контент

| Навык | Назначение |
|-------|------------|
| [`google-discover-optimize`](skills/google-discover-optimize/) | Аудит и оптимизация статей под Google Discover: изображения, E-E-A-T, NewsArticle JSON-LD, мобильные Core Web Vitals. |

### Исследование и факты

| Навык | Назначение |
|-------|------------|
| [`fact-checker`](skills/fact-checker/) | Систематическая проверка фактов и выявление дезинформации с обязательной верификацией источников через веб-поиск. |

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
├── .claude-plugin/     # манифесты плагина (plugin.json, marketplace.json)
├── .github/workflows/  # CI: валидация библиотеки на push и pull request
├── evals/              # роутинг-eval: запрос → ожидаемый навык
├── scripts/            # валидатор, его тесты и прогон eval (stdlib, без venv)
├── skills/
│   ├── advanced-seo-optimizer/
│   ├── agent-workflow/
│   ├── aiogram-bot-auditor/
│   ├── change-review/
│   ├── codebase-recon/
│   ├── dependency-auditor/
│   ├── django-audit/
│   ├── django-tailwind-optimizer/
│   ├── docs-generator/
│   ├── fact-checker/
│   ├── fastapi-architect/
│   ├── git-commit-planner/
│   ├── goal-pipeline/
│   ├── google-discover-optimize/
│   ├── harness-engineering/
│   ├── llm-feature-architect/
│   ├── migration-safety-auditor/
│   ├── obsidian/
│   ├── postgres-performance/
│   ├── python-project-audit/
│   ├── ratchet-loop/
│   ├── release-manager/
│   ├── sage/
│   ├── session-catchup/
│   ├── spec-writer/
│   ├── test-coverage-auditor/
│   ├── test-writer/
│   └── vps-ops/
├── .gitattributes      # нормализация переводов строк (LF)
├── .gitignore
├── CLAUDE.md           # контракт репозитория для агента
├── LICENSE
├── README.md
```

---

## Проверка библиотеки

Инварианты библиотеки (лимит описания, `name` = имя папки, живые ссылки на
`references/`, синхронность README и манифестов, бамп версий) проверяются
скриптом без внешних зависимостей — нужен только Python 3.10+:

```bash
python scripts/validate_skills.py            # гейт: ошибки и предупреждения
python scripts/validate_skills.py --list     # таблица метрик по навыкам
python scripts/validate_skills.py --info     # бэклог качества (не валит сборку)
python scripts/validate_skills.py --strict --check-bump   # режим CI
python scripts/test_validate_skills.py       # тесты самого валидатора
```

Те же проверки выполняет GitHub Actions на каждый push и pull request.

### Роутинг-eval

Валидатор проверяет форму, но не главное: сработает ли навык, когда он нужен.
Это меряет отдельный прогон на обезличенных формулировках из реальной работы
(`evals/routing-cases.jsonl`) — каждый кейс запускается отдельной сессией
`claude -p` в одноразовой песочнице, инструменты правки и сети отключены:

```bash
python scripts/run_routing_eval.py --dry-run   # состав набора, без затрат
python scripts/run_routing_eval.py --tier 1    # прогон подмножества
```

Прогон обращается к API и стоит денег — цена каждого кейса и итог печатаются.
Метрики: **молчит** (навык нужен, но не сработал), **не тот** (сработал
соседний), **ложное срабатывание** (навык не был нужен).

---

## Создание нового навыка

1. Создайте папку с именем навыка в kebab-case.
2. Добавьте `SKILL.md` с фронтматтером (`name` = имя папки) и инструкцией.
3. Вынесите объёмные материалы в `references/` и ссылайтесь на них из `SKILL.md`.
   Конвенция имени справочника выходного формата — `references/output-format.md`.
4. Сформулируйте `description` так, чтобы ассистент понимал, **когда** применять
   навык. Лимит — **1024 символа** (валидация Anthropic); ориентир 600–900:
   что делает → сильные триггер-фразы → разграничение со смежными навыками.
5. Проверьте навык на реальной задаче перед коммитом.
6. Обновите каталог, дерево и бейдж в README и поднимите `version` в
   `.claude-plugin/plugin.json` и `marketplace.json` — иначе кэш маркетплейса
   не увидит изменений.
7. Прогоните `python scripts/validate_skills.py --strict` — он проверит всё
   перечисленное выше и не даст забыть про бамп версий.

Описания навыков в этом репозитории написаны на русском языке, что задаёт язык
взаимодействия по умолчанию; сами навыки работают с задачами на любом языке.

---

## Лицензия

Распространяется по лицензии [MIT](LICENSE). © 2026 Ivan Sinyavskiy.
