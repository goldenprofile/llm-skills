---
name: migration-safety-auditor
description: >
  Аудит безопасности миграций БД (Django migrations и Alembic/SQLAlchemy)
  перед прод-деплоем и помощь в безопасном переписывании: блокировки таблиц,
  downtime, потеря данных, несовместимость старого кода со схемой при
  zero-downtime, опасный backfill, необратимые операции. Postgres и SQLite.
  Используй когда пользователь просит проверить миграцию, спрашивает
  «безопасна ли миграция», «не уронит ли прод», добавляет
  колонку/индекс/constraint на большой таблице, пишет data-миграцию или
  backfill, делает zero-downtime деплой, или упоминает migration review,
  expand/contract, CONCURRENTLY, RunPython.
metadata:
  version: 1.1.0
---

# Migration Safety Auditor

Аудитор безопасности миграций БД перед прод-деплоем. Цель — поймать операции, которые
блокируют таблицу под нагрузкой, ломают работающий код при rolling-деплое, теряют данные
или необратимы. По итогу — отчёт с уровнями риска и (по согласованию) безопасные правки.

## Когда применять

Запускай перед применением миграций на проде, при ревью PR с новой миграцией, при добавлении
колонок/индексов/constraint/FK на непустой таблице, при написании data-миграций и backfill.
Для общего аудита Django см. `django-audit`; этот навык — только про миграции.

## Контекст — установить ПЕРВЫМ делом

Без него оценка риска бессмысленна. Если не ясно из проекта — спроси кратко:

1. **ORM/инструмент**: Django migrations или Alembic/SQLAlchemy. (raw SQL — см. справочник Postgres.)
2. **СУБД**: Postgres или SQLite. Версия Postgres важна (часть операций безопасна с PG 11/12+).
3. **Модель деплоя**: короткий downtime (стоп → миграция → старт) или zero-downtime/rolling
   (старый и новый код работают одновременно). От этого зависит строгость к обратной
   совместимости схемы. См. [references/deploy-models.md](references/deploy-models.md).
4. **Размер затрагиваемых таблиц**: операция, безопасная на 1k строк, кладёт прод на 50M.

## Процесс

1. **Собрать миграции на ревью.** Django: неприменённые файлы в `*/migrations/`,
   `python manage.py makemigrations --check --dry-run`, при сомнениях `sqlmigrate app NNNN`
   для просмотра реального SQL. Alembic: новые ревизии в `versions/`, `alembic upgrade --sql`
   для offline-SQL.
2. **Прогнать каждую операцию по чеклисту рисков** (ниже + справочники).
3. **Классифицировать** по уровню риска, объяснить *почему* опасно именно при его модели деплоя.
4. **Предложить безопасную альтернативу** (expand/contract, CONCURRENTLY, батчи, таймауты).
5. **Отчёт** по [references/report-template.md](references/report-template.md). По согласованию —
   переписать миграции.

## Уровни риска

- **CRITICAL** — гарантированный простой, потеря данных или необратимая операция на проде
  (table rewrite/долгий ACCESS EXCLUSIVE на большой таблице, `DROP COLUMN` с данными, backfill
  всей таблицы одной транзакцией).
- **HIGH** — блокировка записи под нагрузкой или поломка старого кода при zero-downtime
  (индекс без `CONCURRENTLY`, `RENAME`, новый `NOT NULL`/`UNIQUE`/FK без двухфазного приёма).
- **MEDIUM** — нет `lock_timeout`/`statement_timeout`, нет обратной операции
  (`RunPython` без reverse, пустой `downgrade()`), схема и данные смешаны в одной миграции.
- **LOW** — стиль, именование, незначительные улучшения.

## Быстрый чеклист (детали — в справочниках)

- `ADD COLUMN` с volatile/вычисляемым `DEFAULT` или новый `NOT NULL` на непустой таблице → rewrite.
- `CREATE INDEX` без `CONCURRENTLY` → блокирует запись на время построения.
- `ALTER COLUMN TYPE` → почти всегда rewrite + `ACCESS EXCLUSIVE`.
- Добавление `FOREIGN KEY`/`UNIQUE`/`NOT NULL` одним шагом → используй `NOT VALID` → `VALIDATE`.
- `RENAME` колонки/таблицы → ломает работающий старый код; для zero-downtime — expand/contract.
- `DROP COLUMN`/`DROP TABLE` → потеря данных + ломает старый код; только в contract-фазе.
- Backfill/`UPDATE` всей таблицы в одной транзакции → длинные локи, раздувание WAL, реплаг.
- Нет `lock_timeout` перед DDL → миграция ждёт лок и выстраивает очередь ко всей таблице.
- Нет обратной операции → миграцию нельзя откатить при инциденте.

## Справочники

- [references/postgres-operations.md](references/postgres-operations.md) — таблица «операция →
  блокировка → безопасная альтернатива», expand/contract, backfill, таймауты.
- [references/django.md](references/django.md) — Django: `atomic=False`, `AddIndexConcurrently`,
  `RunPython`/reverse, `SeparateDatabaseAndState`, squash, SQLite-нюансы.
- [references/alembic.md](references/alembic.md) — Alembic: ловушки `autogenerate`,
  `batch_alter_table` для SQLite, `autocommit_block`, реальный `downgrade()`.
- [references/deploy-models.md](references/deploy-models.md) — downtime vs zero-downtime,
  expand/contract пошагово, SQLite и переезд на Postgres.
- [references/report-template.md](references/report-template.md) — формат отчёта.
