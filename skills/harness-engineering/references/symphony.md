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

```yaml
---
tracker:
  kind: github            # github | linear | manual
  active_states: "Todo, In Progress"
  terminal_states: "Done, Closed, Cancelled"
polling:
  interval_ms: 30000
workspace:
  root: ./workspaces      # каждая задача = отдельный worktree/директория
hooks:
  after_create: |
    git worktree add . <branch>
    uv sync --all-extras --dev
  before_run: |
    git pull origin main
    make check
  after_run: |
    make check
    git add -A && git commit -m "auto: $ISSUE_ID"
agent:
  max_concurrent_agents: 2   # на одной машине держи низким
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
2. **Hooks** — `after_create` (worktree + install), `before_run` (pull + preflight),
   `after_run` (верификация + коммит), `before_remove` (архивация лога).
3. **State machine**: Unclaimed → Claimed → Running → RetryQueued → Released.
4. **Retry**: continuation при норме, exponential backoff при ошибках.
5. **Concurrency**: при прогоне на одной машине держи `max_concurrent_agents` низким (1-2) —
   иначе локальная машина и БД станут узким местом.
6. **Артефакты верификации**: CI-статус, прогон навык-гейтов, тесты.

## Чеклист Symphony

- [ ] Выбран осознанно (задач достаточно много, они независимы)
- [ ] WORKFLOW.md с валидным YAML front-matter
- [ ] Hooks: минимум after_create и before_run
- [ ] Workspace root указан и доступен
- [ ] Промпт-шаблон использует {{ issue.* }} и {{ attempt }} и ссылается на навык-гейты
- [ ] `max_concurrent_agents` низкий (1-2 при прогоне на одной машине)
- [ ] Retry-стратегия и артефакты верификации описаны

## Антипаттерны

- НЕ включай Symphony, пока базовый harness не доказал надёжность.
- НЕ ставь высокий параллелизм на одной машине с одной БД.
- НЕ давай агенту permissive approval/sandbox в проде; минимальные привилегии.
