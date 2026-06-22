---
name: decision-records
description: Capture architectural and technical decisions as ADR-style notes with context, alternatives considered, and consequences. Lives in the project folder, linked to related tasks.
tags: [obsidian, adr, decisions, architecture, projects]
---

# Decision Records (ADR)

Record architectural and technical decisions with the context that led to them, the
alternatives considered and rejected, and the consequences of the choice. These notes
prevent "why did we do it this way?" amnesia months later.

## Trigger

- User says "запиши решение" / "ADR" / "architecture decision"
- User says "почему выбрали" / "давай зафиксируем" about a technical choice
- After a design discussion that reached a conclusion

## Where it goes

Decision records live **in the project folder** — co-located with tasks and project
docs: `<vault>/projects/<Project>/` (or your vault's equivalent). This keeps context
near the work it affects.

## Workflow

1. **Parse** the decision — extract project, what was decided, why, what alternatives
   were considered
2. **Verify date** — use today's actual date (see SKILL.md → "Дата")
3. **Resolve project folder** — match an existing folder or create a new one
4. **Check for related** — `Grep` for existing decisions on the same topic (may be a
   supersession)
5. **Write note** — ADR format with frontmatter `type: decision`

## Note Format

**Filename:** `YYYY-MM-DD - ADR - Short Decision Title.md`

```markdown
---
type: decision
project: ProjectName
date: YYYY-MM-DD
status: accepted
supersedes: "[[2026-03-01 - ADR - Old Decision]]"
tags: [adr, architecture, project-tag, specific-tag]
---

# ADR: Short Decision Title

## Контекст

[Почему это решение принимается. Какая проблема, какие ограничения, что подтолкнуло. 2-5 предложений.]

## Решение

[Что решили. Чётко, конкретно. 1-3 предложения.]

## Альтернативы

### Вариант A: [название]
- **Плюсы**: ...
- **Минусы**: ...
- **Почему нет**: ...

### Вариант B: [название] (выбранный)
- **Плюсы**: ...
- **Минусы**: ...
- **Почему да**: ...

## Последствия

- Что становится проще
- Что становится сложнее
- Технический долг, который создаётся
- Риски, которые принимаются

## Связанные

- [[2026-06-15 - Task that implements this]]
```

### Frontmatter Fields
- `type` — always `decision`
- `project` — project folder name
- `status` — `proposed` | `accepted` | `deprecated` | `superseded`
- `supersedes` — wikilink to the previous ADR if this replaces one (omit if not)
- `tags` — include `adr` + project tag + technology/specific tags

### Body Guidelines
- Write in Russian by default
- **Контекст** is the most important section — future-you needs WHY, not just WHAT
- **Альтернативы** must include the REJECTED options with honest reasons
- **Последствия** must include negative consequences — decisions without downsides are suspicious
- Keep it concise — an ADR is a snapshot, not a design doc. 1-2 pages max.

## Superseding

When a decision is reversed or replaced:
1. Find the old ADR note
2. `Edit` its `status` to `superseded`
3. Create the new ADR with `supersedes: "[[old-adr]]"`
4. Do NOT delete or rewrite the old ADR — the history is the point

## Pitfalls

- **Recording only the winner**: an ADR with one alternative is useless. The value is in
  what was rejected and why.
- **Retroactive justification**: don't write an ADR that justifies an already-made
  decision without genuine alternatives — that's a doc note, not an ADR.
- **Vague context**: "Решили использовать Redis" without the problem is useless. What
  broke? What was wrong with the current approach?
- **Confusing with tasks**: an ADR captures a DECISION, not work to be done. Link to task
  notes for action items.
- **Date verification**: use today's actual date (see SKILL.md → "Дата").
- **Don't overwrite**: check for an existing ADR on the same topic; prefer supersession.
