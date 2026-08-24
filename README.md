# LLM Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/format-SKILL.md-success.svg)](#authoring-a-skill)
[![Skills: 24](https://img.shields.io/badge/skills-24-informational.svg)](#skill-catalog)

A collection of reusable **Agent Skills** for LLM coding assistants — Claude Code, Codex,
Cursor, Grok, Hermes, OpenCode and other clients of the format. Each skill is a self-contained
instruction in `SKILL.md` format that the assistant loads on demand when a task matches the
description of the skill.

The library targets everyday backend work: auditing and debugging Django, FastAPI and
aiogram projects, database migration safety and PostgreSQL performance, VPS operations and
incident triage, code review, releases, technical SEO, exploring unfamiliar codebases,
organising the work of the agent itself, and note-keeping in Obsidian.

> **A note on language.** Skill instructions and their `description` fields are written in
> Russian, which sets the default language of the interaction. The skills themselves work on
> tasks in any language: the assistant reads the Russian instruction and replies in whatever
> language you use. Translating the skills to English is planned; this README comes first.

---

## What is a skill

A skill is a folder containing a `SKILL.md` file with:

- **YAML frontmatter** with `name` and `description` — the assistant uses the description to
  decide when the skill applies;
- **the instruction body** — the step-by-step process, checklists and rules the agent follows;
- an optional **`references/`** folder with supporting material (report templates, checklists,
  examples) loaded only when needed — the *progressive disclosure* principle.

This keeps the main instruction compact while heavy detail lives in separate files, saving
context.

---

## Compatibility

`SKILL.md` is an open format, originally released by Anthropic and now maintained as a
standard at [agentskills.io](https://agentskills.io). A skill folder is copied into the
skills directory of the relevant client without editing its contents.

| Client | Skills documentation | Directory |
|--------|----------------------|-----------|
| **Claude Code** | [docs](https://code.claude.com/docs/en/skills) | `~/.claude/skills/` (global) or `.claude/skills/` (per project) |
| **OpenCode** | [docs](https://opencode.ai/docs/skills/) | `~/.config/opencode/skills/`, `.opencode/skills/`, and the Claude Code paths above |
| **Codex** | [docs](https://developers.openai.com/codex/skills/) | see docs |
| **Cursor** | [docs](https://cursor.com/docs/context/skills) | see docs |
| **Grok** | — | own marketplace cache in `~/.grok/marketplace-cache/`; clones marketplaces already configured in Claude Code |
| **Hermes** | [docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | see docs |

Many other clients support the format — Gemini CLI, GitHub Copilot, VS Code, Goose, Amp,
Roo Code, Factory, Kiro and more; the current list is the
[client showcase](https://agentskills.io/clients). The folder contents are identical for all
of them; only the destination directory differs.

> One Claude Code install often covers more than one client. OpenCode reads the Claude Code
> skills directories directly. Grok runs its own plugin marketplace, but clones the
> marketplaces it finds configured in Claude Code, so adding this one there makes it show
> up in Grok as well — with a separate cache that has to be refreshed separately.

---

## Install

### As a Claude Code plugin (recommended)

The repository ships plugin manifests (`.claude-plugin/`), so the whole library installs and
updates with one pair of commands:

```
/plugin marketplace add goldenprofile/llm-skills
/plugin install llm-skills@goldenprofile
```

To pick up new releases: `/plugin marketplace update goldenprofile`.

### Manually

Clone the repository and copy the skill folders you want into the skills directory of your
tool. Copy each folder whole, including its `references/`; the folder name must match the
`name` field in the frontmatter.

```bash
git clone https://github.com/goldenprofile/llm-skills.git
cd llm-skills

# Linux / macOS — global for Claude Code (OpenCode reads the same path)
mkdir -p ~/.claude/skills
cp -r skills/django-audit skills/change-review skills/vps-ops ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse skills/django-audit, skills/change-review, skills/vps-ops "$HOME\.claude\skills\"
```

For a **project-level** install put the folders in `.claude/skills/` inside the project
repository — they then reach everyone working on that project.

Once installed, a skill activates automatically when your request matches its description.

---

## Skill catalog

### Django

| Skill | Purpose |
|-------|---------|
| [`django-audit`](skills/django-audit/) | Django audit by lens: architecture, security (OWASP), Celery, code cleanliness, tech debt, deploy readiness, tests. |

### FastAPI

| Skill | Purpose |
|-------|---------|
| [`fastapi-architect`](skills/fastapi-architect/) | FastAPI design and review: structure (APIRouter, lifespan, pydantic-settings), Pydantic v2, async correctness (event-loop blocking, SQLAlchemy 2.x async), DI, tests (httpx + dependency_overrides). |

### Database and migrations

| Skill | Purpose |
|-------|---------|
| [`migration-safety-auditor`](skills/migration-safety-auditor/) | Migration safety before a production deploy (Django + Alembic): table locks, downtime, data loss, backward compatibility for zero-downtime, unsafe backfill. Postgres and SQLite. |
| [`postgres-performance`](skills/postgres-performance/) | PostgreSQL diagnosis and tuning: EXPLAIN ANALYZE, indexes, pg_stat_statements, pgbouncer, autovacuum, memory on a small VPS. |

### Python and code quality

| Skill | Purpose |
|-------|---------|
| [`python-project-audit`](skills/python-project-audit/) | Claimed readiness against actual: unfinished code, critical problems, dead sections. Static analysis (pylint, bandit, mypy, radon, vulture) plus manual review, with a scored report and a verdict. |
| [`test-coverage-auditor`](skills/test-coverage-auditor/) | Test-quality audit for Python/Django: tests without assertions, mocks that verify nothing, uncovered critical paths, skips without a reason. |
| [`change-review`](skills/change-review/) | Deep review of ONE change with an APPROVE / REQUEST CHANGES verdict and a severity scale. Modes: **self** (Claude reviews — correctness, security, reliability, layer boundaries) and **second-opinion** (a different model through the `hermes` CLI: API hallucinations, edge cases, over-engineering). |
| [`dependency-auditor`](skills/dependency-auditor/) | Dependency and supply-chain audit: pip-audit/safety and CVEs, pinning and lockfiles (uv/poetry/pip-tools), safe upgrades with breaking changes called out. |

### Telegram bots (aiogram)

| Skill | Purpose |
|-------|---------|
| [`aiogram-bot-auditor`](skills/aiogram-bot-auditor/) | Audit and guidance for aiogram 3.x bots: Telegram API reliability (flood control 429, blocks, single instance), architecture (Router/middlewares/FSM), deployment (polling under systemd, webhook + nginx, RedisStorage) and tests. |

### Deployment and infrastructure

| Skill | Purpose |
|-------|---------|
| [`vps-ops`](skills/vps-ops/) | Running Python apps on a single VPS without Docker (nginx + systemd + postgres + redis) in three modes: **deploy** (configs and deployment audit), **observe** (Sentry, healthchecks, logs, alerts), **triage** (incident runbook: 502/504, restart loops, disk, postgres). |

### Codebase analysis

| Skill | Purpose |
|-------|---------|
| [`codebase-recon`](skills/codebase-recon/) | Codebase reconnaissance in two modes: **whole** (an unfamiliar project end to end — stack, entry points, data flows, business goal) and **subject** (one area or feature, with a current-versus-desired gap analysis). Read-only. |

### Agent workflow

| Skill | Purpose |
|-------|---------|
| [`agent-workflow`](skills/agent-workflow/) | Working on the agent itself, in five modes: **delegate** (do it myself or hand it over, which mode and model), **decompose** (split a task into single-pass chunks), **prompt** (turn loose wording into an unambiguous brief), **context** (session degradation, knowledge layers, a CLAUDE.md checklist), **audit** (retrospective: repeated mistakes, stale docs, guardrails). |
| [`git-commit-planner`](skills/git-commit-planner/) | Reads the working tree and plans logical atomic commits instead of one monolithic one. |
| [`release-manager`](skills/release-manager/) | Releases: semver from the diff, CHANGELOG from Conventional Commits, git tags and GitHub Releases, a pre-release checklist and smoke test. |
| [`session-catchup`](skills/session-catchup/) | Resuming interrupted work: rebuilding context from git, state files and the conversation history. |
| [`harness-engineering`](skills/harness-engineering/) | Harness for a Python project so agents can work in it: Makefile, CI (GitHub Actions), `ARCHITECTURE.md`, `CLAUDE.md`/`AGENTS.md` sync, and a Definition of Done that calls the other skills in this library. Owns the canonical Makefile target namespace. |
| [`goal-pipeline`](skills/goal-pipeline/) | A planner-executor on top of the native Claude Code `/goal`: light recon, splitting a brownfield task into phases with measurable criteria, quality gates wired in per phase type (migration-safety-auditor, /code-review, pyright, test-coverage-auditor), one ready `/goal` line, and an audit against the original plan. |
| [`ratchet-loop`](skills/ratchet-loop/) | An in-session ratchet: pushes ONE measurable scalar (latency, SQL query count, bundle size, pass rate) as far as it goes — keeps only the changes that improved it and reverts the rest through git. Frozen evaluator (anti-Goodhart) plus an independent verifier pass; it does not self-terminate, it runs to a budget or a plateau. |

### Documentation

| Skill | Purpose |
|-------|---------|
| [`docs-generator`](skills/docs-generator/) | Documentation: README, ADRs, docstrings (Google style) and `CLAUDE.md`/`AGENTS.md` sync. Writes what is missing and flags what has gone stale. |
| [`sage`](skills/sage/) | Virtual-team coordinator: a raw input (draft, post, diagram) becomes a package of documents (summary, discussion, design/runbook). Not a single spec. |
| [`spec-writer`](skills/spec-writer/) | Project documents in three modes: spec (problem, goals, architecture, ADR decisions, risks), plan (phases, estimates, dependencies) and brief (a note for management, no code). |

### Notes and knowledge

| Skill | Purpose |
|-------|---------|
| [`obsidian`](skills/obsidian/) | Working with an Obsidian vault (filesystem-first): clippings, project tasks with status, ADRs, a work journal, project briefs, research synthesis, reviews, and analysis of the tag and link graph. |

### SEO and content

| Skill | Purpose |
|-------|---------|
| [`advanced-seo-optimizer`](skills/advanced-seo-optimizer/) | Technical SEO audit for server-rendered HTML in Django and FastAPI (Jinja2): semantics, meta/OG, Schema.org JSON-LD, robots/sitemap, hreflang, Core Web Vitals, AI crawlers and llms.txt. Includes a Google Discover lens: `max-image-preview`, E-E-A-T, NewsArticle, RSS. |

### Frontend and design

| Skill | Purpose |
|-------|---------|
| [`ui-dna`](skills/ui-dna/) | Turns the visual language of a live site into measured values via `getComputedStyle`: palette, fonts and weights, type scale, spacing, radii, CSS variables, component signatures. Modes extract and compare. |

---

## Validating the library

Library invariants (description limit, `name` matching the folder, live links into
`references/`, README and manifests in sync, version bumps) are checked by a script with no
external dependencies — Python 3.10+ is all it needs:

```bash
python scripts/validate_skills.py            # gate: errors and warnings
python scripts/validate_skills.py --list     # per-skill metrics table
python scripts/validate_skills.py --info     # quality backlog (does not fail the build)
python scripts/validate_skills.py --strict --check-bump   # CI mode
python scripts/test_validate_skills.py       # tests for the validator itself
```

GitHub Actions runs the same checks on every push and pull request.

### Routing eval

The validator checks shape, not the thing that matters: whether a skill fires when it is
needed. That is measured by a separate run over anonymised phrasings taken from real work
(`evals/routing-cases.jsonl`). Each case runs as its own `claude -p` session in a disposable
sandbox with editing and network tools disabled:

```bash
python scripts/run_routing_eval.py --dry-run   # what is in the set, at no cost
python scripts/run_routing_eval.py --tier 1    # run a subset
```

The run calls the API and costs money — the price of each case and the total are printed.
Metrics: **silent** (the skill was needed and did not fire), **wrong one** (a neighbour fired),
**false positive** (the skill was not needed).

---

## Authoring a skill

A skill folder looks like this:

```
<skill-name>/
├── SKILL.md            # required: frontmatter + instruction
└── references/         # optional: material loaded on demand
    ├── checklist.md
    └── template.md
```

A minimal `SKILL.md`:

```markdown
---
name: my-skill
description: >
  Briefly — what the skill does and WHEN to apply it. The assistant matches on this
  description, so state the triggers explicitly ("use when the user asks …").
  At least ~20 characters.
---

# My Skill

The step-by-step instruction the agent follows…
```

To add one:

1. Create a folder named in kebab-case; `name` in the frontmatter must match it.
2. Write `SKILL.md`: frontmatter plus the instruction.
3. Move bulky material into `references/` and link to it from `SKILL.md`. The conventional
   name for the output-format reference is `references/output-format.md`.
4. Write the `description` so the assistant understands **when** to apply the skill. The limit
   is **1024 characters** (Anthropic validation); aim for 600–900: what it does → strong
   trigger phrases → how it differs from neighbouring skills.
5. Try the skill on a real task before committing.
6. Update the catalog and the badge in this README, and bump `version` in
   `.claude-plugin/plugin.json` and `marketplace.json` — otherwise the marketplace cache will
   not see the change.
7. Run `python scripts/validate_skills.py --strict`, which checks all of the above and will
   not let you forget the version bump.

---

## Repository layout

| Path | Contents |
|------|----------|
| `skills/` | one folder per skill — the library itself |
| `references/` (inside a skill) | material loaded on demand |
| `.claude-plugin/` | plugin manifests (`plugin.json`, `marketplace.json`) |
| `evals/` | routing eval: prompt → expected skill |
| `scripts/` | validator, its tests and the eval runner (stdlib only, no venv) |
| `.github/workflows/` | CI: library validation on push and pull request |
| `CLAUDE.md` | the repository contract for the agent |

---

## License

Released under the [MIT](LICENSE) license. © 2026 Ivan Sinyavskiy.
