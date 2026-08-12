---
name: review-mode
description: Periodic vault review — find stale tasks, unprocessed inbox items, dead projects, and completed work to archive. Produces an actionable report, respects incremental execution.
tags: [obsidian, review, stale, cleanup, inbox, periodic]
---

# Review Mode

Periodic review of the vault to surface what needs attention: stale tasks, unprocessed
inbox items, dead projects, completed work ripe for archival. Not a structural audit
(that's Vault Zen) — this is a **time-based health check**.

## Trigger

- User says "ревью" / "что зависло" / "недельный итог" / "почистить inbox"
- User says "что у нас протухло" / "надо ли что-то закрыть"
- User asks for a periodic freshness checkup on vault health

## Scope

Two concerns (map the zones onto your vault's actual folders — see SKILL.md):

| Zone | Path | What to check |
|------|------|---------------|
| Projects | `<vault>/projects/` | Stale tasks, dead projects, unarchived completions |
| Inbox | `<vault>/inbox/` | Unprocessed clippings, duplicates |

## Workflow

### 1. Stale Tasks Scan (projects)

`Grep` for `status: (todo|in-progress)` (`glob: "*.md"`, `path` = `<vault>/projects`).
For each match, read the `date` field from frontmatter. Flag:
- **2+ weeks old** (todo/in-progress) → 🟡 likely abandoned
- **1+ month old** (todo/in-progress) → 🔴 probably dead, suggest archive or cancel
- **3+ months old** (done) → should be archived

### 2. Inbox Check

`Glob` the inbox zone (`inbox/**/*.md`):
- Count total clippings
- Find the 5 oldest — are they processed (tags, structured body) or raw dumps?
- Check for duplicates: similar titles on the same dates

### 3. Project Activity

For each project folder under the projects zone:
- Find the most recent file (by date in filename or frontmatter)
- If last activity > 2 months → flag as "possibly inactive"
- Count open vs done tasks

### 4. Decision Hygiene

`Grep` for `type: decision` (`glob: "*.md"`, `path` = `<vault>/projects`):
- `status: proposed` older than 1 week → needs resolution
- `status: accepted` but no linked tasks → implementation not started?

### 5. Compile Report

## Report Format

Output in Russian:

```
## 🔍 Ревью хранилища — YYYY-MM-DD

### ⏰ Протухшие задачи (N)

#### 🔴 Мёртвые (1+ месяц, todo/in-progress)
1. [[Task Title]] — проект: X, дата: 2026-04-15 (2 месяца назад)
   → Рекомендация: закрыть как cancelled или разблокировать

#### 🟡 Возможно забытые (2+ недели, todo/in-progress)
1. [[Task Title]] — проект: Y, дата: 2026-06-01

### 📥 Inbox
- Всего клиппингов: N
- Самые старые необработанные: 3 файла (даты)
- Дубликаты: 2 пары (по похожим заголовкам)

### 💀 Неактивные проекты
- **ProjectX** — последняя активность: 2026-03-15 (3 месяца назад)
  → Рассмотреть архивирование

### ✅ Готово к архивации (done, 3+ месяца)
- [[Task]] — закрыт 2026-03-01

### 📋 План действий
1. [ ] Закрыть/разблокировать N мёртвых задач
2. [ ] Обработать N необработанных клиппингов
3. [ ] Заархивировать N выполненных задач
4. [ ] Решить судьбу N неактивных проектов

**Итого:** N пунктов, из них M критичных (🔴)
```

## Execution Mode

Same as Vault Zen — **analysis only by default**, execute on request.

- **Analysis only** (default): report findings, let the user decide
- **Execute** (on "сделай" / "примени" / "почисти"):
  1. Process items **by category** (stale tasks → inbox → archive)
  2. Ask confirmation per category batch — users prefer "частями"
  3. Task status updates: `Edit` the frontmatter `status` field
  4. Archival: move to an `Архив/` subfolder within the project
  5. Report results after each batch

## Time Thresholds (Configurable)

| Concern | Yellow | Red |
|---------|--------|-----|
| todo/in-progress task | 2+ weeks | 1+ month |
| done task (archive candidate) | 2+ months | 3+ months |
| proposed decision | 3+ days | 1+ week |
| Project inactivity | 1+ month | 2+ months |
| Unprocessed clipping | 1+ week | 2+ weeks |

## Pitfalls

- **Don't auto-archive**: always confirm before changing status or moving files. The
  report is advisory.
- **Date sensitivity**: the whole review is date-driven. Use today's actual date (see
  SKILL.md → "Дата").
- **False positives**: a task dated 2 months ago might be intentionally long-term. Read
  it before flagging — check if `priority: low`.
- **Respect incremental execution**: process one category, report, ask to continue.
- **Don't touch project docs**: only flag tasks and decisions; overview files are always
  relevant.
- **Vault Zen overlap**: if the vault has structural issues (misplaced files, naming
  chaos), mention it briefly and point to Vault Zen — don't mix structural audit into a
  time-based review.
