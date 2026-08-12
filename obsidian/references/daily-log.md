---
name: daily-log
description: Retrospective work journal capturing what was accomplished, decisions made, blockers hit, and next steps. Distinct from tasks (forward-looking) — this is context recovery between sessions.
tags: [obsidian, journal, daily, log, retrospective]
---

# Daily Log

Capture a retrospective snapshot of work: what was done, what was decided, what blocked
progress, and what's next. Unlike tasks (forward-looking), the daily log is for
**context recovery** — answering "what did we do last time?" without re-reading the
entire session.

## Trigger

- User says "лог дня" / "что сделали" / "итоги" / "daily" / "запиши итоги"
- User asks to summarize what was accomplished in the current session
- User says "сохрани контекст" / "запиши прогресс" at the end of a work session
- Proactively offered at the end of a long productive session

## Where it goes

Default: a central logs zone, `<vault>/logs/` (or your vault's equivalent). Per-project
logs (`<vault>/projects/<Project>/log/`) only if the session was exclusively one project.

## Workflow

1. **Gather** — reconstruct the session:
   - Tasks created/updated (`Grep` for `type: task` notes with today's date)
   - Decisions recorded (`Grep` for `type: decision` notes with today's date)
   - Clippings saved today
   - Code changes (if available: `git log --since="today 00:00" --oneline`)
   - Vault files created/modified today (`Glob` + check dates)
2. **Verify date** — use today's actual date (see SKILL.md → "Дата")
3. **Synthesize** — don't just list items; group by theme/project, note the narrative
4. **Write note** — daily-log format with frontmatter

## Note Format

**Filename:** `YYYY-MM-DD.md` (one log per day)

```markdown
---
type: daily-log
date: YYYY-MM-DD
projects: [ProjectA, ProjectB]
tags: [daily-log, project-tag1, project-tag2]
---

# YYYY-MM-DD

## Что сделано

### ProjectA
- Конкретное достижение 1
  → [[2026-06-22 - Task Note]]

### ProjectB
- Конкретное достижение
  → [[2026-06-22 - Related Task]]

## Решения

- Выбрали X вместо Y потому что ... → [[2026-06-22 - ADR - Decision Title]]
- Согласились отложить Z до следующей итерации

## Блокеры

- Блокер 1 — что мешает, что нужно для разблокировки
- (если блокеров нет — секцию не писать)

## Заметки

- Неформальные наблюдения, инсайты, "в следующий раз учесть ..."

## Дальше

- [ ] Next action 1 → [[task-note]]
- [ ] Next action 2
```

### Frontmatter Fields
- `type` — always `daily-log`
- `date` — the log's date
- `projects` — list of projects touched during the day
- `tags` — include `daily-log` + project tags

### Body Guidelines
- Write in Russian by default
- **Что сделано** — concrete outcomes. "Исправили race condition в Celery worker" >
  "разбирались с Celery"
- **Link to artifacts** — `[[wikilinks]]` to task notes, ADRs, clippings created today.
  The log is a hub, not a replacement for individual notes
- **Решения** — even informal ones that didn't get a full ADR. "Решили не делать" counts
- **Блокеры** — only if they exist. Empty sections are noise
- **Дальше** — 3-5 items max. This is the handoff to the next session
- **Don't duplicate** — if a task note has the detail, the log just references it

## Gathering from the Current Session

At the end of a session:
1. Review what was accomplished and which tools were used
2. List today's vault artifacts with `Glob` + date filter
3. If git repos are involved, run `git log --since="today 00:00" --oneline`
4. Synthesize into the log format above

## Pitfalls

- **Listing instead of narrating**: "Создали 3 файла. Закрыли 2 задачи." is useless.
  Group by theme, note what mattered and what was hard.
- **Missing links**: a log without wikilinks to its artifacts is an island. Link everything.
- **Too verbose**: the log is a summary. If it's longer than ~50 lines, push detail into
  task/ADR notes and link them.
- **Date verification**: use today's actual date (see SKILL.md → "Дата").
- **Don't overwrite**: if `YYYY-MM-DD.md` exists, append new sections (`Edit`) rather
  than replacing.
- **Empty sections**: omit Блокеры/Решения/Заметки if there's nothing — don't write "нет".
