# Symphony — оркестрация (опционально, на малом потоке задач избыточна)

Symphony = автономные прогоны задач: трекер → изоляция → хуки → retry → верификация артефактов.
При небольшом потоке задач это обычно **overkill**: ценность появляется, когда задач много и они
независимы. Сначала доведи базовый harness (Фазы 1–4 в SKILL.md), Symphony — только осознанно.

## Минимальный вариант (рекомендуется вместо полного Symphony)

Не поднимай оркестратор с трекером и пулом агентов. Достаточно:

1. **Изоляция через git worktree** — каждая независимая задача в своём worktree, чтобы не
   мешать рабочему дереву (см. навык про worktrees, если есть).
2. **Гейт = `make check` + навык-гейты из DoD** — тот же набор проверок, что и в обычной работе.
3. **Коммиты — через `git-commit-planner`**, ревью — через `change-review`.

Это даёт автономию уровня 2 (агент готовит изменения, ты approve/merge) без инфраструктуры.

## Полный WORKFLOW.md (если задач реально много)

Создавай только при явном выборе «Harness + Symphony». Конфиг — YAML front-matter + промпт-шаблон:

Схема меняется — **сверяй конфиг с актуальной**
[SPEC](https://github.com/openai/symphony/blob/main/SPEC.md) перед генерацией, а не по памяти.

```yaml
---
tracker:
  kind: github            # github | linear | manual
  active_states:          # СПИСКИ строк, не строка через запятую
    - "Todo"
    - "In Progress"
  terminal_states:
    - "Done"
    - "Closed"
    - "Cancelled"
  provider: {}            # ключи задаёт адаптер трекера — смотри его доку
polling:
  interval_ms: 30000
workspace:
  root: ./workspaces      # каждая задача = отдельный worktree/директория
hooks:
  timeout_ms: 600000      # ОДИН лимит на все хуки; дефолт 60 000 мс мал для `uv sync`
  after_create: git worktree add . <branch> && uv sync --all-extras --dev
  before_run: git pull origin main && make check
  after_run: make check   # ТОЛЬКО верификация — про коммит см. ниже
agent:
  max_concurrent_agents: 2   # на одной машине держи низким (дефолт спеки — 10)
  max_turns: 20
  max_retry_backoff_ms: 300000
---

## Промпт-шаблон
Задача {{ issue.identifier }}: {{ issue.title }}
{% if issue.description %}### Описание
{{ issue.description }}{% endif %}
{% if attempt %}### Повтор #{{ attempt }}
Предыдущая попытка не прошла — проанализируй причину и смени подход.{% endif %}

### Требования
1. Изменения в рамках одной задачи
2. `make check` проходит (включая sec)
3. Затронуты миграции → прогнать migration-safety-auditor
4. Новый код покрыт тестами
5. Коммит: "feat/fix(scope): short imperative description [{{ issue.identifier }}]"
```

## Ключевые концепции (для адаптации)

1. **Workspace isolation** — задача в своём worktree/директории.
2. **Hooks** — `after_create` (worktree + install, только на новом workspace),
   `before_run` (pull + preflight; его падение отменяет попытку), `after_run` (верификация),
   `before_remove` (архивация лога). У `after_run` и `before_remove` падения логируются и
   игнорируются — гейтом они не работают.
3. **State machine**: Unclaimed → Claimed → Running → RetryQueued → Released.
4. **Retry**: continuation при норме, exponential backoff при ошибках.
5. **Concurrency**: при прогоне на одной машине держи `max_concurrent_agents` низким (1-2) —
   иначе локальная машина и БД станут узким местом.
6. **Артефакты верификации**: CI-статус, прогон навык-гейтов, тесты.

## Чеклист Symphony

- [ ] Выбран осознанно (задач достаточно много, они независимы)
- [ ] WORKFLOW.md сверен с актуальной SPEC: **валидный YAML ≠ рабочая конфигурация**
      (состояния — списки, `hooks.timeout_ms` покрывает установку зависимостей,
      в `after_run` нет коммита)
- [ ] Hooks: минимум after_create и before_run
- [ ] Workspace root указан и доступен
- [ ] Промпт-шаблон использует {{ issue.* }} и {{ attempt }} и ссылается на навык-гейты
- [ ] `max_concurrent_agents` низкий (1-2 при прогоне на одной машине)
- [ ] Retry-стратегия и артефакты верификации описаны

## Антипаттерны

- **НЕ коммить из `after_run`.** По SPEC он срабатывает после *каждой* попытки — включая
  падение, таймаут и отмену, — а его собственные ошибки игнорируются. `git add -A && git commit`
  здесь однажды уедет с недоделанной работой, и никто не узнает. Коммит делает агент внутри
  прогона по DoD; хук — только проверяет. По той же причине не полагайся на «`make check` строкой
  выше»: без `&&` следующая команда выполнится и на красном гейте.
- НЕ включай Symphony, пока базовый harness не доказал надёжность.
- НЕ ставь высокий параллелизм на одной машине с одной БД.
- НЕ давай агенту permissive approval/sandbox в проде; минимальные привилегии.
