---
name: dependency-auditor
description: >
  Аудит зависимостей и supply-chain безопасности Python-проектов и помощь в безопасном
  обновлении. Находит уязвимые пакеты (CVE через pip-audit/safety), слабый пиннинг и
  отсутствие lockfile, неразделённые prod/dev-зависимости, устаревшие/заброшенные пакеты,
  риски транзитивных зависимостей и typosquatting. Помогает обновлять пакеты по semver
  без поломок (по одному/батчами, чтение breaking changes, тесты, откат). Используй когда
  пользователь просит проверить зависимости, спрашивает «безопасны ли мои пакеты», «есть ли
  уязвимости», «что обновить», обновляет requirements/pyproject, видит алерт Dependabot/CVE,
  настраивает lockfile или воспроизводимые сборки, или упоминает pip-audit, safety, uv.lock,
  poetry.lock, pip-tools, supply chain. Менеджеры uv/pip/poetry.
metadata:
  version: 1.0.0
---

# Dependency Auditor

Аудитор зависимостей и supply-chain безопасности Python-проектов. Цель — найти уязвимые,
устаревшие, заброшенные и плохо запиненные пакеты, оценить риск и помочь обновить их
безопасно: по semver, с чтением breaking changes, прогоном тестов и возможностью отката.
По итогу — отчёт с уровнями риска и (по согласованию) конкретные правки.

## Когда применять

Перед релизом/деплоем, при алерте Dependabot/CVE, при ревью изменений в `requirements*.txt`/
`pyproject.toml`/lockfile, при настройке воспроизводимых сборок, при плановом обновлении.
Для общего аудита проекта см. `python-project-audit`; этот навык — только про зависимости.

## Контекст — установить ПЕРВЫМ делом

1. **Менеджер пакетов**: uv, pip (+ pip-tools), poetry. Определяет lockfile и команды апгрейда.
2. **Источник истины зависимостей**: `pyproject.toml`, `requirements.txt`/`requirements.in`,
   `uv.lock`/`poetry.lock`. Есть ли вообще lockfile и хеши.
3. **Окружение**: прод vs dev/test; отделены ли dev-зависимости (`--extra`/`--group`/`[dev]`).
4. **Есть ли тесты и CI**: можно ли проверить апгрейд прогоном (см. `test-coverage-auditor`).

## Процесс

1. **Инвентаризация.** Собрать манифесты и lockfiles, зафиксировать активный менеджер,
   получить полное дерево: `uv pip list` / `pip list`, `uv tree` / `pipdeptree` / `poetry show --tree`.
2. **Скан уязвимостей.** `pip-audit` (и при наличии — `safety scan`); читать severity и
   fix-версии. См. [references/scanning.md](references/scanning.md).
3. **Проверка пиннинга/lockfile.** Запинено ли, есть ли хеши, разделены ли prod/dev,
   воспроизводима ли установка. См. [references/pinning-lockfiles.md](references/pinning-lockfiles.md).
4. **Устаревшие/заброшенные.** `pip list --outdated` / `uv tree --outdated`; оценить заброшенность
   и typosquatting (см. scanning.md).
5. **Классифицировать** по риску, объяснить *почему* опасно именно здесь.
6. **План безопасного апгрейда** по [references/upgrades.md](references/upgrades.md).
7. **Отчёт** по [references/output-format.md](references/output-format.md). По согласованию — правки.

## Уровни риска

- **CRITICAL** — известная уязвимость с эксплойтом/RCE/утечкой в **прод**-зависимости при
  наличии fix-версии; явный typosquat/скомпрометированный пакет в зависимостях.
- **HIGH** — CVE средней/высокой severity в прод-пути; нет lockfile вообще при деплое на прод;
  установка из непиннутого диапазона (невоспроизводимый прод); заброшенный прод-пакет с
  открытой уязвимостью без патча.
- **MEDIUM** — CVE только в dev/test-зависимостях; устаревший на мажор пакет без known-CVE;
  prod и dev не разделены; lockfile без хешей; сильно отставшие, но не уязвимые пакеты.
- **LOW** — мелкие апдейты в пределах patch/minor, стиль пиннинга, отсутствие проверки лицензий.

## Быстрый чеклист

- Прогонялся `pip-audit` (и `safety`)? Есть ли CVE с доступным fix? Прод или только dev?
- Есть **lockfile** (`uv.lock`/`poetry.lock`/`requirements.txt` с хешами) и он закоммичен?
- Установка воспроизводима: `uv sync --frozen` / `pip install --require-hashes` / `poetry install`?
- Прямые прод-зависимости запинены осознанно (не голый `*`, не случайный `latest`)?
- Dev/test отделены от прода (`--group dev` / `[project.optional-dependencies]` / `requirements-dev.txt`)?
- Есть устаревшие на мажор или заброшенные (нет релизов >1–2 лет) пакеты в проде?
- Имена пакетов соответствуют реальным (нет typosquat: `python-requests`, `djnago`, `urlib3`)?
- После апгрейда прогоняются тесты? Зафиксирован ли способ отката (старый lockfile)?

## Связь с библиотекой навыков

- `python-project-audit` — общий аудит проекта; здесь — только зависимости и supply chain.
- `harness-engineering` — `make sec` в CI (bandit + pip-audit); этот навык даёт содержание шага.
- `test-coverage-auditor` — прогон/качество тестов после апгрейда (обязательный шаг апгрейда).
- `techlead-ai` — ревью диффа правок зависимостей перед мержем.

## Справочники

- [references/scanning.md](references/scanning.md) — pip-audit/safety: команды, флаги, чтение
  вывода, severity, что делать с CVE; устаревшие, заброшенные, typosquatting.
- [references/pinning-lockfiles.md](references/pinning-lockfiles.md) — стратегии пиннинга,
  lockfiles по инструментам (uv/poetry/pip-tools), хеши, воспроизводимость, prod/dev split.
- [references/upgrades.md](references/upgrades.md) — рабочий процесс обновления, semver,
  breaking changes, батчи vs по одному, тесты, откат.
- [references/output-format.md](references/output-format.md) — формат отчёта.
