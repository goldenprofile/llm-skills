---
name: project-brief
description: Generate an on-demand snapshot of a project's current state from vault data — active tasks, recent decisions, risks, and next steps. Not a saved file; a live query over the vault.
tags: [obsidian, project, brief, dashboard, status, context-recovery]
---

# Project Brief

Generate a live status snapshot for a project from vault data. This is **not a saved
file** — it's a query over the project folder that produces a structured brief. Think
of it as `git status` for project knowledge.

## Trigger

- User says "контекст по проекту" / "бриф" / "статус проекта" / "что по X"
- User says "освежи контекст" / "где мы" about a specific project
- User asks "что осталось сделать по X" / "какие открытые задачи по Y"

## Where to look

The project root under the projects zone: `<vault>/projects/<Project>/` (or your
vault's equivalent). Resolve the vault root per SKILL.md → "Путь к хранилищу".

## Workflow

1. **Resolve project** — match the name to a folder under the projects zone (`Glob`
   `projects/*`). If not found, ask the user.
2. **Inventory** — list all files in the project folder with `Glob`
   (`projects/<Project>/**/*.md`)
3. **Categorize** — determine each file's type from frontmatter:
   - `type: task` → task note (check `status`)
   - `type: decision` → ADR (check `status`)
   - `type: daily-log` → log entry
   - no frontmatter or `type: project` → project doc
4. **Sample** — read the 3-5 most recent notes (by date in filename or frontmatter)
5. **Synthesize** — produce the brief (format below)
6. **Don't save** — output as a response. Save only if the user explicitly asks
   ("сохрани бриф").

## Brief Format

Output in Russian:

```
## 📋 Бриф: <Project>

**Файлов в проекте:** N | **Задач:** X (todo: A, in-progress: B, done: C) | **Решений:** D

### Активные задачи

| Статус | Задача | Дата |
|--------|--------|------|
| 🔵 todo | [[Task Title]] | 2026-06-15 |
| 🟡 in-progress | [[Task Title]] | 2026-06-10 |

(если задач больше 10 — показать все todo/in-progress, done отдельной строкой)

### Последние решения

- [[ADR Title]] — краткая суть (2026-06-20)

### Риски и блокеры

- Задача в in-progress 2+ недели: [[Task]] (2026-06-01)
- Решение без задач-последствий: [[ADR]] — реализация не начата?
- (если рисков нет — секцию не выводить)

### Последняя активность

- 2026-06-22 — [[Daily Log]] — "что делали"
- 2026-06-20 — последний ADR

### Рекомендация

1-3 предложения: на чём сфокусироваться, что протухло, что требует внимания.
```

## Adjustment by Project Size

| Files | Approach |
|-------|----------|
| 1-5 | Read all files, detailed brief |
| 5-15 | All filenames + 3-5 most recent files |
| 15-30 | All filenames + 2-3 most recent + statistical (status counts) |
| 30+ | Statistical only — counts by type/status, top 5 active tasks; ask whether to focus |

## Cross-Zone Links

If the project has related clippings elsewhere (e.g. the inbox zone), find them with
`Grep` for the project tag (`glob: "*.md"`, `path` = `<vault>/inbox/`). Include a
"Связанные материалы" section with the 3-5 most relevant clippings if found.

## Pitfalls

- **Don't save unless asked**: the brief is a live query. A saved snapshot goes stale
  tomorrow. If the user wants it saved, add `type: brief` frontmatter and warn it's
  point-in-time.
- **Stale data**: if the most recent file is 3+ months old, flag "Проект неактивен с <date>".
- **Missing frontmatter**: files without `type` are ambiguous — categorize by content and
  note the count of uncategorized files.
- **Project name disambiguation**: if multiple folders match, ask which one.
- **Don't read everything for large projects**: 30+ files — use filenames and frontmatter only.
- **Wikilinks in output**: use `[[Note Name]]` so the user can click through in Obsidian.
