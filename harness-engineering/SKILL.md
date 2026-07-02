---
name: harness-engineering
description: >
  Внедрение harness engineering (обвязки для AI-агентов) в Python-проект
  соло-разработчика: Django, FastAPI, aiogram. Создаёт Makefile, CI (GitHub
  Actions), ARCHITECTURE.md, обновляет CLAUDE.md/AGENTS.md (DoD, tooling,
  canonical docs) и вшивает в Definition of Done вызовы навыков библиотеки
  (migration-safety-auditor, python-project-audit, test-coverage-auditor) и
  официальных гейтов (/code-review, /security-review, pyright-lsp).
  Деплой-ориентир — systemd/nginx/redis/postgres, не Docker. Используй когда
  пользователь просит настроить harness, подготовить проект для агентов,
  внедрить DoD/tooling-обвязку, или говорит «harness», «symphony»,
  «оркестрация агентов».
metadata:
  version: 1.4.0
---

# Harness Engineering — обвязка проекта для AI-агентов (соло)

Ты — инженер среды для AI-агентов. Цель: сделать так, чтобы агент работал по проверяемым
правилам, а проверка была автоматической. Профиль владельца — **один разработчик + агенты**
(Claude Code и OpenCode), стек **Python: Django / FastAPI / aiogram-боты**, среда **Windows**,
деплой **systemd + nginx + redis + postgres** (Docker — меньшинство проектов).

## Принципы

- **Менять нужно среду, а не модель.** Harness = команды + ограничения + циклы проверки.
- **Если правило нельзя проверить автоматически — его нет.** Enforcement (CI/линтер/тест) > документация.
- **Минимализм.** Policy-файл — карта на 1–2 экрана, не энциклопедия. Лишний контекст вредит.
- **Память трёхслойна, committed policy переносим.** Память Claude Code: личное на все проекты
  (`~/.claude/CLAUDE.md`) ↔ проектное в репо (`./CLAUDE.md`, **должно быть OS-переносимым**) ↔
  проектное+машинное вне репо (`./CLAUDE.local.md`, gitignored). Машинная специфика («я на
  Windows, сервисы на удалённом Linux, не дёргай systemctl») в committed-файл **не кладётся** —
  на другой ОС она ложна и навязывается всем. Рантайм формулируй как факт проекта («нужны
  Postgres+Redis»), не как «ты на Windows».
- **Соло ≠ команда.** «Ревьюер» — это ты + навык `techlead-ai`, а не другой человек. Гейты —
  автоматические, а не межчеловеческие.
- **Harness — дирижёр твоей библиотеки навыков и официальных гейтов.** DoD не «напиши хорошо», а «прогони такой-то навык/гейт».

## Процесс

### Фаза 1 — Разведка
Определи: класс проекта (Django-веб / FastAPI-API / aiogram-бот / automation-скрипт), менеджер
пакетов (uv/pip/poetry), что уже есть из обвязки (CLAUDE.md, AGENTS.md, Makefile, CI,
ARCHITECTURE.md), какие линтер/типизатор/тесты реально настроены и проходят.

### Фаза 2 — План (gap-таблица)
Войди в режим плана. Сверь текущее состояние с [чеклистом](#чеклист-готовности) и покажи gap.
Согласуй объём: **базовый harness** (по умолчанию) или **+ Symphony** (опционально, чаще
overkill для соло — см. [references/symphony.md](references/symphony.md)).

### Фаза 3 — Реализация (по иерархии источников истины)

0. **Аудит существующей policy (до создания нового!).** Если `CLAUDE.md`/`AGENTS.md` уже есть —
   не дописывай аддитивно. Сначала **прочитай и вычисти**: машинно-специфичное → в
   `~/.claude/CLAUDE.md` или `CLAUDE.local.md`; устаревшее/протухшие ссылки → убрать; дубли того,
   что проверяет CI → убрать. Аддитивное применение навыка поверх раздутого файла — частая ошибка
   (см. Антипаттерны).
1. **Enforcement** — три уровня, от сильного к слабому:
   - **Makefile** (работает и на Windows, и на Unix) + **CI**. Цели под Python-стек
     (`lint`/`fmt`/`type`/`test`/`sec`/`all`) и под класс проекта. Полные шаблоны:
     [references/tooling.md](references/tooling.md).
   - **Hooks** (`.claude/settings.json` → `hooks`) — enforcement, не зависящий от того, вспомнит
     ли агент про Makefile. `PreToolUse` может **заблокировать** вызов (exit 2 / JSON `deny`),
     `PostToolUse` — среагировать на правку (прогнать линт на изменённом файле и вернуть результат).
     Это и есть «среда не даёт забыть». Паттерны: [references/policy-and-docs.md](references/policy-and-docs.md).
   - **Permissions** (`.claude/settings.json` → `permissions.allow`) — allowlist на `make`/`uv run`,
     чтобы агент не ловил промпты на безопасных целях (быстрый старт — `/fewer-permission-prompts`).
2. **Policy** — память **трёхслойна** (см. Принципы): committed `./CLAUDE.md` держит только
   **переносимое** (Tooling, MUST NOT, DoD, Canonical Docs, инварианты); машинное — в
   `~/.claude/CLAUDE.md`/`CLAUDE.local.md`. `AGENTS.md` — **тонкий указатель** на `CLAUDE.md`
   (не копия/симлинк: копия разъезжается, симлинк на Windows ненадёжен). Длинные доки подключай
   импортом `@ARCHITECTURE.md`, а не копипастой. Шаблоны: [references/policy-and-docs.md](references/policy-and-docs.md).
3. **Architecture** — `ARCHITECTURE.md`: границы модулей, инварианты, reference-примеры.
4. **Lessons** — `tasks/lessons.md`: цикл «ошибка агента → правило → проверка».
5. **Symphony** — только если выбрано: [references/symphony.md](references/symphony.md).

### Фаза 4 — Верификация
1. **Гейт существует ≠ гейт работает.** Прогони `make lint`/`type` (на Windows — без БД) и убедись,
   что `make test` хотя бы **коллектит** (для Django: `[tool.pytest.ini_options]` с
   `DJANGO_SETTINGS_MODULE` и `pythonpath`/`extra-paths`, если приложения лежат в `sys.path`).
   Частый провал: тесты вроде есть, но pytest их не собирает.
2. **На легаси не «чини всё красное».** Сними **baseline** (сколько ошибок lint/format/type),
   применяй только безопасные автофиксы, остальное — в ROADMAP/lessons как долг с **ratchet**
   (CI падает на *новом*, не на всём legacy). «Зелёный `make all`» на зрелом проекте — цель, а не
   предусловие сдачи harness.
3. Запиши пойманные грабли в `tasks/lessons.md`. Если создан WORKFLOW.md — проверь, что YAML парсится.

## Definition of Done — вшить вызовы навыков и гейтов

Это главная оптимизация под твою библиотеку. DoD проекта (в CLAUDE.md/AGENTS.md) делай
**трёхслойным**: дешёвая автоматика → быстрые гейты диффа на каждый коммит → глубокие
навык-гейты перед релизом и по запросу. Принцип anti-collision: при пересечении выбирай
более узкий/быстрый гейт; тяжёлые опции — opt-in, не по умолчанию.

**Автоматика (CI + локально):**
- `make all` — `lint`/`type`/`test`/`sec` зелёные. Типы прямо в сессии — **`pyright-lsp`**
  (батч-гейт остаётся `make type`).

**Перед каждым коммитом — быстрые гейты диффа:**
- **`/code-review`** — баги уровня строк + переиспользование/упрощение (`--fix` применяет
  правки, `--comment` — инлайн в PR; `ultra` — только для крупных/рискованных веток).
- **`/security-review`** — безопасность диффа.
- разбивка на коммиты — навык **`git-commit-planner`**.

**Перед релизом / по запросу — глубокие навык-гейты:**
- **`techlead-ai`** — глубокое архитектурное ревью; вызывать ЯВНО на крупном/рискованном
  диффе, а не после каждой правки (не дублировать `/code-review`).
- **`test-coverage-auditor`** — качество тестов (assertion'ы, моки без проверок).
- **`migration-safety-auditor`** — если затронуты миграции, до деплоя на прод.
- **`python-project-audit`** — production readiness перед деплоем; для Django —
  **`django-audit`** (в т.ч. security-линза, OWASP проектного уровня).

Слэш-команды (`/code-review`, `/security-review`) — гейты Claude Code; в OpenCode их роль
закрывают `make sec` + навыки `techlead-ai` / `django-audit` (security).

Так harness становится оркестратором: дешёвое ловит CI, дифф — быстрые официальные гейты,
а глубину и production-готовность — твои навыки.

## Чеклист готовности

**Базовый harness (обязательно):**
- [ ] `Makefile` с целями `lint/fmt/type/test/sec/all` + цели класса проекта
- [ ] CI (GitHub Actions): джобы по capability — `lint`+`type` (без сервисов), `test`
      (с Postgres/Redis), `sec`; safe-by-default до настройки секретов; actions пиннятся по SHA
- [ ] `.claude/settings.json` — `permissions.allow` на `make`/`uv run` + хук `PostToolUse`
      (линт изменённого файла); опц. `PreToolUse` на рискованные `Bash`
- [ ] committed `CLAUDE.md` **переносим** (без машинной специфики); машинное — в
      `~/.claude/CLAUDE.md`/`CLAUDE.local.md` (последний в `.gitignore`); `AGENTS.md` — тонкий указатель
- [ ] Policy ≤ 1–2 экранов; DoD ссылается на твои навыки и официальные гейты (см. выше)
- [ ] `ARCHITECTURE.md` (границы, инварианты, reference-примеры); подключён `@import`-ом, не копипастой
- [ ] `tasks/lessons.md` инициализирован
- [ ] Деплой-заметка под systemd/nginx (не навязывать Docker)
- [ ] Гейты не только существуют, но и **запускаются** (pytest коллектит; `make lint`/`type` зелёные
      или с зафиксированным baseline)

**Symphony (опционально):** см. чеклист в [references/symphony.md](references/symphony.md).

## Антипаттерны

- НЕ раздувай policy и НЕ дублируй в нём то, что проверяет CI.
- НЕ навязывай Symphony соло-проекту — сначала базовый harness.
- НЕ навязывай Docker и многостековые таблицы — стек известен (Python), среда Windows.
- НЕ предполагай, что каждый проект — веб-сервис: у aiogram-ботов нет HTTP-эндпоинтов и свой
  жизненный цикл (polling-воркер под systemd).
- НЕ ломай существующий код ради «чистоты» — минимальное воздействие.
- НЕ клади машинно/OS-специфичное («ты на Windows», «сервисы на удалённом Ubuntu», `systemctl`) в
  committed `CLAUDE.md` — на другой ОС это ложь. Только `~/.claude/CLAUDE.md` или `CLAUDE.local.md`.
- НЕ применяй навык **аддитивно** поверх существующего раздутого policy — сначала аудит и прунинг
  (Фаза 3, шаг 0).
- НЕ делай `permissions.allow` широким (`Bash(*)`): широкий allowlist → агент штампует подтверждения
  не глядя, и слой перестаёт защищать. Узкие цели (`make`/`uv run`); что блокировать `PreToolUse` —
  таксономия deny-категорий в [references/policy-and-docs.md](references/policy-and-docs.md).
- НЕ вешай `ruff check --fix` на общий `fmt`: в Django «неиспользуемый» импорт часто регистрирует
  сигналы/админку (side-effect) — слепой автофикс их сносит. Формат и автофикс — раздельно.
- НЕ считай «гейт создан» = «гейт работает»: проверь, что pytest реально коллектит, а CI-джоба с БД
  поднимает сервисы.

## Растущая автономия (соло)

```
Уровень 0: агент пишет код, ты проверяешь всё вручную
Уровень 1: harness → make all + навык-гейты проверяют автоматически, ты ревьюишь дифф
Уровень 2: Symphony → агент сам берёт задачи и готовит коммиты, ты approve/merge
Уровень 3: full auto в доверенной среде (обычно избыточно для соло)
```
Не прыгай через уровни: каждый стоит на доказанной надёжности предыдущего.
