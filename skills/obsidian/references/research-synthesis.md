---
name: research-synthesis
description: Synthesize multiple vault sources (clippings, notes, tasks) and optional external sources into a coherent themed research note with thesis, evidence, contradictions, and open questions.
tags: [obsidian, research, synthesis, knowledge]
---

# Research Synthesis

Synthesize information from multiple sources into a coherent themed note. Unlike
clippings (single-source capture), synthesis merges several sources into a unified
narrative with a thesis.

## Trigger

- User asks to compare/synthesize/summarize multiple sources
- User says "сравни" / "синтезируй" / "что известно про X" / "собери по теме"
- User provides multiple clippings, URLs, or topics and wants a unified summary
- User asks "какие есть подходы к X" or "что думают про Y"

## Where it goes

Save synthesis notes under the vault's research/inbox zone, e.g.
`<vault>/inbox/research/` (or your vault's equivalent). Resolve the vault root per
SKILL.md → "Путь к хранилищу".

## Workflow

### 1. Gather sources

- **From vault**: `Grep` for the topic keywords (`glob: "*.md"`, `path` = vault) to find
  existing clippings/notes
- **From current context**: clippings the user just shared, URLs in the message
- **From web** (if asked): fetch additional sources with `WebFetch`
- Read each source fully — synthesis quality depends on depth, don't skim

### 2. Analyze

For each source, extract:
- **Key claim(s)** — the author's main point
- **Evidence** — data, benchmarks, examples, citations
- **Stance** — positive/negative/neutral on the topic
- **Date** — how fresh is it? Weight recent sources higher

### 3. Identify patterns

- **Consensus** — what do most sources agree on?
- **Contradictions** — where do they disagree? (the most valuable section)
- **Gaps** — what questions remain unanswered?
- **Evolution** — has the consensus shifted over time?

### 4. Write synthesis

Formulate a **thesis** — your synthesized understanding, not just a list of sources.
The thesis is the value-add of synthesis.

## Note Format

**Filename:** `YYYY-MM-DD - Research - Short Topic.md`

```markdown
---
type: research
date: YYYY-MM-DD
topic: Short Topic
sources:
  - "[[2026-06-15 - Source One]]"
  - "https://example.com/external-source"
tags: [research, topic-tag, tag2]
---

# Research: Topic

## Тезис

[1-3 предложения — синтезированное понимание темы. Не пересказ источников, а вывод из их сопоставления.]

## Консенсус

- Point 1 — поддерживается [Source A], [Source B]
- Point 2 — ...

## Противоречия

- **Вопрос X**: [Source A] утверждает ..., тогда как [Source B] считает ...
- **Вопрос Y**: ...

## Контекст и нюансы

[Важные оговорки, условия применимости, зависимости от контекста.]

## Открытые вопросы

- [Неразрешённый вопрос 1]

## Источники

- [[Source One]] — кратко: что дало
- [External URL](URL) — кратко: что дало
```

### Frontmatter Fields
- `type` — always `research`
- `topic` — short topic identifier
- `sources` — vault notes (`[[wikilinks]]`) and/or external URLs used
- `tags` — 3-7 tags, always include `research`

### Body Guidelines
- Write in Russian by default
- Link to source notes with `[[wikilinks]]` — don't just name them
- Put direct quotes in `>` blockquotes with attribution
- Represent each author's actual position — don't paraphrase their intent
- The **Тезис** is mandatory — if you can't formulate one, you've collected, not synthesized

## Pitfalls

- **No thesis = not synthesis**: "Source A says X. Source B says Y." with no synthesized
  understanding is a collection. Rewrite with a thesis.
- **Cherry-picking**: present contradicting views honestly.
- **Stale sources**: a 2023 source on LLM capabilities is already ancient — note the date
  and weight accordingly.
- **Missing wikilinks**: link vault sources, include URLs for external ones. Never lose the trail.
- **Date verification**: use today's actual date (see SKILL.md → "Дата").
- **Scope creep**: if the topic is too broad ("AI in general"), narrow it to a focused question.
- **External fetch failures**: if a web source is Cloudflare-protected or paywalled, note
  it and proceed with the available sources.
