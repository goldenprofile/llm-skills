---
name: tag-link-graph
description: Analyze tag taxonomy health, detect orphaned notes (no incoming wikilinks), propose cross-links between related notes, and generate Maps of Content (MOC). Deeper than Vault Zen's linkage dimension.
tags: [obsidian, tags, links, graph, orphan, moc, taxonomy]
---

# Tag & Link Graph

Analyze the vault's knowledge graph: tag taxonomy health, orphaned notes, missing
cross-links, and MOC (Map of Content) opportunities. Where Vault Zen checks the
structure of **files and folders**, this lens checks the structure of **connections**.

## Trigger

- User says "карта знаний" / "orphan" / "MOC" / "связи" / "теги в хаосе"
- User says "что не связано ни с чем" / "битые ссылки"
- User asks "какие теги дублируются" / "наведи порядок в тегах"
- User wants a knowledge map / overview of the vault

## Scope

Run on the whole vault, one subfolder, or both. Resolve the vault root per SKILL.md →
"Путь к хранилищу". Default: the current working vault.

## Workflow

### 1. Tag Extraction

`Grep` for `^tags:` (`glob: "*.md"`, `path` = vault), then read each match to parse the
full `tags:` field (inline list or YAML array). Build a tag index: `{ tag: [file1, ...] }`.

### 2. Tag Taxonomy Health

- **Duplicate/variant tags**: `myproject` vs `MyProject` vs `my-project` — normalize and flag
- **Over-granular tags**: tags used on only 1 file — useful or noise?
- **Over-broad tags**: `ai` on 50+ files — too broad for navigation
- **Inconsistent casing**: `Django` vs `django` vs `Django-framework`
- **Hyphenation inconsistency**: `claude-code` vs `claudecode` vs `claude_code`
- **Tag drift**: the same concept tagged differently over time (check dates)

### 3. Orphan Detection

An orphan = a note with **no incoming wikilinks** (nothing links TO it).

`Grep` for `\[\[Note Name` across the vault to find backlinks. Optimization: extract all
`[[wikilink]]` references from all files first, then compute the inverse — don't search
per-note (too slow for 100+ files).

Categories:
- **True orphan**: no incoming links, not referenced anywhere
- **Sink**: has incoming links but links to nothing (dead end)
- **Hub**: links to many notes but few link back (MOC candidate)

### 4. Broken Links

`[[Note Name]]` pointing to a file that doesn't exist. Extract all wikilink targets,
check each against the file index.

### 5. Cross-Link Suggestions

Find notes that share 3+ tags but are NOT linked to each other:
```
For each pair of notes with tag overlap >= 3:
  if not linked (no [[NoteA]] in NoteB and vice versa):
    suggest cross-link
```
Limit to the top 10-15 most relevant (highest tag overlap, most recent).

### 6. MOC Generation (Optional)

A MOC (Map of Content) is a hub note that organizes related notes. Generate when a tag
cluster has 5+ notes, or the user asks for a "карта" / "MOC".

MOC format:
```markdown
---
type: moc
topic: Topic Name
date: YYYY-MM-DD
auto_generated: true
tags: [moc, topic-tag]
---

# MOC: Topic Name

## Обзор

[1-2 предложения — что в этой карте, почему эти заметки вместе.]

## Основное

- [[Note 1]] — кратко: о чём
- [[Note 2]] — кратко: о чём

## По подтемам

### Subtopic A
- [[Note 4]]
```

`Write` MOCs to the maps zone (`<vault>/maps/`).

## Report Format

Output in Russian:

```
## 🕸️ Анализ графа связей — <scope>

**Заметок:** N | **Уникальных тегов:** M | **Wikilinks:** K | **Орфанов:** O

### 🏷️ Теги

#### Дубликаты/варианты (требуют нормализации)
| Тег | Файлов | Варианты |
|-----|--------|----------|
| myproject | 8 | MyProject (3), my-project (1) |

#### Слишком широкие (20+ файлов)
- `ai` — 45 файлов (рассмотреть разбиение на подтеги)

#### Одиночные (1 файл — возможно шум)
- `one-off-tag` — [[Note]]

### 🔗 Связи

#### Орфаны (нет входящих ссылок) — N заметок
1. [[Note Name]] — tags: [tag1, tag2]

#### Битые ссылки — M
1. `[[Nonexistent Note]]` ← [[Source Note]]

#### Предложения кросс-ссылок (топ 10)
1. [[Note A]] ↔ [[Note B]] — общих тегов: 4 (tag1, tag2, tag3, tag4)

### 🗺️ MOC-кандидаты
- **"Topic X"** — 7 заметок с тегом `topic-x` → предложить MOC

### 📋 План действий
1. [ ] Нормализовать N дубликатов тегов
2. [ ] Связать N орфанов с релевантными заметками
3. [ ] Починить N битых ссылок
4. [ ] Создать MOC для "Topic X" (опционально)
```

## Execution Mode

- **Analysis only** (default): report findings
- **Tag normalization**: `Edit` the frontmatter `tags:` field across affected files
- **Cross-linking**: `Edit` to add `[[wikilinks]]` to note bodies (at the end or under a
  `## Связанные` section)
- **MOC generation**: `Write` to the maps zone — only if the user confirms

Always work **частями** — one category at a time, report, ask to continue.

## Pitfalls

- **Performance on large vaults**: extracting all wikilinks from 100+ files is expensive.
  For big vaults, run a small Python script via `Bash` to batch-read and compute the
  graph in one pass rather than many per-note `Grep` calls.
- **Tag normalization is destructive**: changing `MyProject` to `myproject` across 8
  files is a batch operation — verify with the user first. Some casing may be intentional.
- **Cross-link suggestions can be wrong**: two notes sharing `python` and `django` might
  be about different aspects. Review each suggestion — don't auto-link.
- **MOCs go stale**: a MOC generated today is outdated next week. Note `auto_generated:
  true` + `date` in frontmatter and offer to regenerate.
- **Broken-link false positives**: `[[Note Name|alias]]` — the target is `Note Name`,
  not `alias`. Parse aliases correctly.
- **Don't touch `.obsidian/`**: plugin config may define tag hierarchies. Respect it.
- **Tag extraction edge cases**: inline tags (`#tag` in body) vs frontmatter `tags:`.
  Obsidian supports both — search both.
