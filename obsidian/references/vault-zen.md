---
name: vault-zen
description: Analyze Obsidian vault directories for optimal placement, structure, naming, relevance, and overall organization. Propose improvements to reach "vault zen".
tags: [obsidian, audit, organization, structure, zen]
---

# Vault Zen — Structural Analysis & Optimization

Analyze a vault directory (and its subdirectories) to evaluate placement, structure,
naming consistency, relevance, and redundancy. Produce actionable recommendations to
bring the vault to a state of "zen" — clean, navigable, scalable.

## Trigger

- User asks to analyze/audit a directory or project folder
- User says "аудит" / "структура" / "дзен" / "порядок" / "разобрать" about vault org
- User asks "как лучше организовать" / "куда положить" / "что тут лишнее"

## Scope Resolution

Resolve the target before analysis:

1. **Project folder** — e.g. `projects/<Project>/` → this project's organization
2. **Zone** — e.g. `projects/` → cross-project structure
3. **Entire vault** — vault root → full audit (heavier; warn about scope)
4. **Specific subdirectory** — focused analysis of one section

Default scope: recursive. If the user says "только эту папку" — non-recursive.

## Workflow

### 1. Inventory

- List all files recursively with `Glob` (`**/*` under the target dir)
- Capture for each: path, filename, extension
- Build a mental tree: subdirectories, depth, file types, naming patterns
- Skip noise: `.obsidian/`, attachment folders (binary), `.git/`, `node_modules/`

### 2. Structural Analysis

Evaluate against seven dimensions. (Zone names below are roles — map them onto your
vault's actual folder names; see SKILL.md → "Структура папок".)

#### A. Placement

Are files in the correct top-level zone?

| Zone | Role | What belongs here |
|------|------|-------------------|
| Projects | `projects/<Project>/` | Tasks, project docs, audits, plans |
| Inbox | `inbox/` | External content, articles, shared snippets |
| Maps | `maps/` | Dashboards, project/task maps |
| Attachments | `attachments/` | Media files |
| Meta | `meta/` | Vault-level config, templates |

**Red flags:** attachments inside project folders instead of the attachments zone;
clippings in a project folder; random notes in the vault root; files from project A in
project B's folder.

#### B. Hierarchy & Structure

- **Depth**: 2-3 levels is healthy; 4+ needs justification
- **Subfolder purpose**: each subfolder should have one clear purpose. Good: `Analysis/`,
  `Архив/`. Bad: an opaque name you can't decode without opening it
- **Flat dumps**: 15+ files with no subfolders — candidates for grouping by topic/date/status
- **Empty or near-empty**: a folder with only an overview note — active or archive?
- **Single-child folders**: one file in a folder — usually unnecessary nesting

#### C. Naming Consistency

- **Task notes**: should follow `YYYY-MM-DD - Title.md`. Flag deviations like
  `05.11.2025.md`, `dc.md`, `Без названия.md`
- **Date formats**: `2026-06-15` (ISO, correct) vs `15.06.2026` vs ambiguous `05.11.2025`.
  ISO is the standard
- **Non-descriptive names**: `dc.md`, `Без названия 1.md` — read content, propose names
- **Language mix**: Russian + English filenames are fine; flag inconsistent patterns
- **Title casing**: pick a convention and flag mixes

#### D. Frontmatter Health

Sample 5-10 files and check:

- **Missing frontmatter**: structured notes (tasks, clippings) without a YAML block
- **Inconsistent fields**: some tasks have `priority`, others don't
- **Status values**: `in-progress` vs `in_progress` vs `в работе` — pick one
- **Tags**: duplicates, casing, typos
- **Type field**: is `type: task` present? Distinguishes tasks from docs

#### E. Relevance & Freshness

- **Stale tasks**: `todo`/`in-progress` 2+ months old — likely abandoned
- **Superseded files**: `План v1.md` + `План v2.md` — old version → `Архив/`?
- **Untitled drafts**: `Без названия.md` — usually abandoned; read, then rename/merge/delete
- **Dead project markers**: a project folder with no recent activity → suggest archiving

#### F. Redundancy & Overlap

- **Similar titles**: overlapping scope?
- **Content overlap**: read suspect files and check if they cover the same ground
- **Split content**: `Часть 1.md`, `Часть 2.md` — merge unless there's a clear reason
- **Duplicate attachments**: same image in multiple locations

#### G. Linkage

- **Orphaned notes**: no incoming `[[wikilinks]]`. Check with `Grep` for `\[\[NoteName`
- **Broken links**: `[[Note Name]]` pointing to a non-existent file
- **Missing cross-links**: task notes that should link to a project overview but don't
- **Isolated clusters**: groups that link to each other but nothing else

### 3. Report Format

Produce the analysis as a structured response (in Russian). Do NOT write a file unless
the user explicitly asks to save the report.

```
## 🔍 Аудит: <directory>

**Обзор:** N файлов, M папок, макс. глубина X уровней
**Health:** 🟢 Чисто / 🟡 Есть что улучшить / 🔴 Требует внимания

### 📊 Разбивка
- Задач: N (todo: X, in-progress: Y, done: Z)
- Документов: N
- Черновиков/без названия: N
- Вложений вне attachments: N

### 🔴 Критичные проблемы
1. [Проблема] → [Конкретная рекомендация]
   `путь/к/файлу.md`

### 🟡 Рекомендации
1. [Проблема] → [Рекомендация]
   `путь/к/файлу.md`

### 🟢 Что хорошо
1. [Что работает] — сохранять

### 📋 План действий (по приоритету)
1. [ ] [Действие] → `путь`
2. [ ] [Действие] → `путь`
```

### 4. Analysis Depth

| Files | Approach |
|-------|----------|
| 1-10 | Read every file, deep analysis |
| 10-30 | Read all filenames + sample 5-10 files for content/frontmatter |
| 30-100 | Filenames + sample 5 files + statistical (naming, dates, frontmatter) |
| 100+ | Statistical only — patterns, structure, counts. Warn that a full deep-read is expensive; offer to zoom into specific subdirectories |

## Recommendations Guidelines

- **Be specific**: "Переименовать `dc.md` → `2026-06-15 - Конфигурация доменов.md`"
- **Preserve user intent**: never suggest deleting content without confirmation —
  propose archiving instead
- **Respect existing structure**: evolution > revolution. Don't propose radical
  reorganization unless fundamentally broken
- **Each recommendation actionable**: executable in 1-2 tool calls
- **Prioritize**: Critical (misplaced files, broken structure) → Quality (naming,
  frontmatter) → Polish (cross-links, orphans)
- **Explain the "why"** briefly for each recommendation

## Execution Mode

- **Analysis only** (default): report findings, let the user decide
- **Analysis + execute**: if the user says "сделай" / "примени" / "наведи порядок":
  1. Rename files (check for incoming wikilinks first!)
  2. Move misplaced files
  3. Archive stale content (move to `Архив/` subfolder)
  4. Fix frontmatter (`Edit`)
  5. Confirm each destructive action (delete/move) unless told "без подтверждения"

### Execution Heuristics

- **Stub files (< 100 bytes)**: in legacy vaults these are almost always stubs — a
  single URL, a trivial command, or an empty skeleton. Read each, but expect most to be
  deletable. Don't propose "fleshing them out".
- **`Без названия*.md` / `Untitled*.md` triage**: Obsidian's default names for new
  notes — very common in legacy inbox folders. For each: read content, then categorize
  as delete (empty/garbage) / rename in-place / move + rename (belongs to a project).
- **Phased execution**: with 5+ independent items, execute one at a time with user
  approval between phases. Don't batch-execute everything at once.

### Incremental execution

Many users prefer working "частями" — execute in batches, report results, then proceed.
After each batch: report what was done, verify file counts, and ask to continue.

### Project consolidation preference

When a file clearly belongs to a known project, prefer **moving it to the project
folder** over renaming in-place in a legacy directory. Offer the choice; default to
moving unless the file is genuinely project-agnostic.

## Pitfalls

- **Moving files: use absolute paths for BOTH source and destination.** With `Bash mv`
  or PowerShell `Move-Item`, a bare destination filename resolves to the current working
  directory, not the source's directory — the file silently lands in the wrong place.
  Always pass full paths: `mv "<vault>/old.md" "<vault>/new.md"`.
- **Verify after each batch**: after deletes/moves/renames, re-list with `Glob` to
  confirm expected counts. Catches misplaced files before they compound.
- **Don't analyze attachment folders**: binary files, no structure. Skip them.
- **Don't touch `.obsidian/`**: plugin config — leave it alone.
- **Wikilink safety**: before renaming ANY file, `Grep` for `[[OldName]]` across the
  vault. Broken links are worse than bad names. If links exist, update them all or don't rename.
- **Respect overview notes**: an intentional project overview file is not clutter.
- **Read before judging**: `Без названия.md` might hold valuable content. Read first.
- **Don't over-engineer**: 5 well-named files in a flat folder is fine. "Zen" = clean,
  not over-organized.
- **Ambiguous legacy dates**: when renaming files with partial dates (`4 августа.md`),
  the year is often not inferable from the name. Check the parent folder structure, then
  the content for temporal clues. If still unclear, ASK — don't guess. (Different from
  the "verify today's date" rule: here you're determining a historical date.)
- **Abbreviations in folder names may be meaningful**: codes or names like `DEL`, `OLD`,
  `TMP` in a folder name don't necessarily mean "safe to delete". When in doubt, ask.
- **Language**: analysis and recommendations in Russian.
- **Triage before proposing**: don't dump 15 issues. Group by severity, present the top
  5-7 actionable items, mention "ещё N мелких улучшений" at the end.
