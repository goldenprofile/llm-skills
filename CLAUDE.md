# CLAUDE.md — llm-skills

Контракт репозитория живёт в **[AGENTS.md](AGENTS.md)** — прочитай его первым.

Кратко, самое важное:

- Гейт перед коммитом: `python scripts/validate_skills.py --strict`, затем
  `python scripts/test_validate_skills.py`.
- Правил описание навыка — роутинг-eval: `python scripts/run_routing_eval.py --tier 1`.
- Навыки лежат в `skills/<name>/`; манифесты — `.claude-plugin/plugin.json`
  и `marketplace.json`, версия бампится синхронно с `metadata.version` навыка.
- Планирование — GitHub Issues, ROADMAP-файла нет и не заводить.
- Описание навыка — дискриминатор, а не аннотация; имена навыков не
  переименовывать; `scripts/` — только stdlib.

Полные правила (инварианты, стоимость системного промта, язык,
переносимость, целевой профиль) — в AGENTS.md.
