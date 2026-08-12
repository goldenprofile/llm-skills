---
name: obsidian-tasks
description: Save project tasks into an Obsidian vault as structured Markdown notes with YAML frontmatter, status tracking, and project-based organization.
tags: [obsidian, tasks, projects, productivity]
---

# Obsidian Tasks

Save project tasks into the vault as structured Markdown notes with metadata, status
tracking, and project-based organization.

## Trigger

- User sends a task in the form `ProjectName: Task description`
- User asks to create/add/save a task for a project
- User says "задача" / "таск" / "добавь задачу" in the context of a project task

## Where it goes

Tasks live in the project's folder under the vault's projects zone (see SKILL.md →
"Структура папок"): `<vault>/projects/<ProjectName>/<filename>.md` (or your vault's
equivalent, e.g. `2-PROJECTS/`).

**Resolve the project folder** by listing existing project folders with `Glob`
(`projects/*`). Match the task's project name to an existing folder; if none matches,
**create the folder** — the user may be starting a new project. Preserve the user's
casing for folder names.

## Workflow

1. **Parse** the message — extract the project name and the task description
2. **Verify date** — use today's actual date (see SKILL.md → "Дата")
3. **Resolve project folder** — match an existing folder or create a new one
4. **Check for duplicates** — `Grep`/`Glob` the project folder for similar task titles;
   if found, ask whether to update or create new
5. **Generate** a short task title and tags from the description
6. **Write note** — `Write` a Markdown file with YAML frontmatter

## Input Formats

### Short form
```
MyApp: Проверить текущий статус проекта и подготовить к деплою реализованные фичи.
```
→ Project: `MyApp`, Task: full description after the colon

### Detailed form
```
my-site.ru: Проанализировать шаблон карточки события на предмет вывода задвоенных
данных из экземпляров класса Exhibition (parent) и Event (child)
```
→ Project: `my-site.ru`, Task: full technical description

### Multi-line with context
```
my-site.ru: Реализовать автопродление подписки
Надо добавить periodic task через Celery или cron
Ссылка на тикет: https://example.com/issues/123
```
→ Project: `my-site.ru`, Task title + body details + links section

### Multiple tasks at once
```
MyApp: Проверить статус проекта
MyApp: Подготовить фичи к деплою
my-site.ru: Исправить задвоение данных в карточке
```
→ Create separate notes for each task

## Note Format

**Filename:** `YYYY-MM-DD - Short Title.md`

**Template:**
```markdown
---
type: task
project: ProjectName
status: todo
priority: normal
date: YYYY-MM-DD
tags: [tag1, tag2]
---

# Short Title

[Full task description — copy the user's wording verbatim, preserving technical details]

## Контекст

[Optional: background info, why this task exists, related issues]

## Ссылки

- [Link description](URL)
```

### Frontmatter Fields
- `type` — always `task` (distinguishes from project docs, audits, etc.)
- `project` — project folder name
- `status` — `todo` | `in-progress` | `done` | `cancelled` (default: `todo`)
- `priority` — `low` | `normal` | `high` | `critical` (default: `normal`)
- `date` — date the task was created
- `tags` — auto-generated (2-5 tags, project-specific)

### Body Guidelines
- **Title**: concise, action-oriented (imperative verb: "Проверить", "Реализовать")
- **Description**: preserve the user's wording and technical specifics — don't paraphrase
- **Контекст**: add only if the user provides background beyond the core task
- **Ссылки**: add only if the user provides URLs; omit otherwise
- Write in Russian by default (matching the user's language)

## Status Updates

When the user says a task is done or in progress:
- Find the task file in the project folder
- `Edit` the `status` field in frontmatter
- Do NOT rename the file — keep the original filename for link stability

## Batch Tasks

When the user sends multiple tasks:
- Create a separate note for each
- For 3+ tasks, process without per-task confirmation — just report the batch result

## Tags

- 2-5 tags per task
- Always include the project name as a tag (lowercase, hyphenated)
- Common clusters: `deploy`, `bug`, `refactoring`, `feature`, `admin`, `api`,
  `database`, `ui`, `agent`

## Priority Detection

Default is `normal`. Upgrade to:
- `high` — "срочно" / "важно" / "быстро" / "надо поскорее"
- `critical` — "критично" / "блокер" / "всё стоит из-за этого"
- `low` — "когда-нибудь" / "не спеша" / "на будущее"

## Pitfalls

- **Wrong date**: the date in filename AND frontmatter must be today's actual date
  (see SKILL.md → "Дата"). The #1 recurring mistake is a stale/guessed date.
- **Don't overwrite existing notes**: check for files with the same date+title first.
- **Project name case**: preserve the user's casing for folder names.
- **Preserve technical details**: copy class names, file paths, API endpoints verbatim.
- **💡 Заметка/Рекомендация**: after the task description, add a `## 💡 Заметка`
  section with one brief useful insight — a recommendation, pitfall, tool suggestion,
  or architectural observation relevant to the task. Not a full solution; a quick
  "heads up" (1-5 sentences). Omit only if there's genuinely nothing useful to add.
- **No empty sections**: no links → no `## Ссылки`; no extra context → no `## Контекст`.
- **Task vs project note**: project folders may hold project docs (`type: project`),
  audits, etc. Only create notes with `type: task`; don't overwrite other content.
