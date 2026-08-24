# Postgres: операции, блокировки, безопасные альтернативы

Источник большинства проблем — DDL берёт `ACCESS EXCLUSIVE` lock (блокирует *всё*, включая
чтение) и/или переписывает таблицу целиком (table rewrite). Дополнительная ловушка —
**очередь блокировок**: даже мгновенный `ACCESS EXCLUSIVE` сначала ждёт завершения текущих
запросов к таблице, а пока ждёт — блокирует все новые запросы. Поэтому «быстрая» операция
на нагруженной таблице может остановить её на время самого долгого активного запроса.

Версии Postgres имеют значение: многие операции стали безопасными в PG 11 и PG 12.

## Таблица операций

| Операция | Риск | Почему | Безопасная альтернатива |
|----------|------|--------|--------------------------|
| `ADD COLUMN` без default | LOW | Метаданные, мгновенно | Безопасно |
| `ADD COLUMN` с **константным** default | LOW (PG 11+) | PG 11+ хранит default в каталоге, без rewrite | Безопасно на PG 11+. На PG ≤10 — rewrite |
| `ADD COLUMN` с **volatile/вычисляемым** default (`now()`, `uuid_generate_v4()`) | CRITICAL | Table rewrite под `ACCESS EXCLUSIVE` | Добавить колонку nullable → backfill батчами → выставить default отдельно |
| `ADD COLUMN ... NOT NULL` без default на непустой таблице | CRITICAL | Ошибка или rewrite | Колонка nullable → backfill → `NOT NULL` через `NOT VALID`/`VALIDATE` |
| `ALTER COLUMN SET NOT NULL` | HIGH | Полный скан под `ACCESS EXCLUSIVE` (PG ≤11) | PG 12+: `ADD CONSTRAINT chk CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` → `SET NOT NULL` (подхватит constraint быстро) |
| `CREATE INDEX` (без `CONCURRENTLY`) | HIGH | `SHARE` lock — блокирует запись на всё время построения | `CREATE INDEX CONCURRENTLY` (вне транзакции; см. ниже) |
| `ALTER COLUMN TYPE` | CRITICAL | Почти всегда rewrite + `ACCESS EXCLUSIVE` | Новая колонка → backfill → переключение (expand/contract). Иногда безопасно: `varchar(n)`→`text`, увеличение `varchar(n)` |
| `ADD FOREIGN KEY` (валидируемый сразу) | HIGH | `SHARE ROW EXCLUSIVE` на обеих таблицах + скан на валидацию | `ADD CONSTRAINT ... NOT VALID` (быстро) → отдельным шагом `VALIDATE CONSTRAINT` (`SHARE UPDATE EXCLUSIVE`, не блокирует DML) |
| `ADD UNIQUE constraint` напрямую | HIGH | Строит unique-индекс под локом | `CREATE UNIQUE INDEX CONCURRENTLY` → `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX` |
| `ADD CHECK constraint` | MEDIUM | Скан на валидацию под локом | `ADD CONSTRAINT ... NOT VALID` → `VALIDATE CONSTRAINT` |
| `DROP COLUMN` | HIGH | Метаданные (быстро), но теряет данные и ломает `SELECT *`/старый код | Только contract-фаза после деплоя кода, не читающего колонку |
| `RENAME COLUMN` / `RENAME TABLE` | HIGH | Мгновенно, но мгновенно ломает работающий старый код | Не для zero-downtime. Expand/contract: новая колонка + двойная запись |
| `DROP TABLE` / `TRUNCATE` | CRITICAL | Потеря данных, `TRUNCATE` берёт `ACCESS EXCLUSIVE` | Только после подтверждения, что ничего не читает; бэкап |
| Backfill `UPDATE` всей таблицы | CRITICAL | Длинные row-локи, раздувание WAL, лаг реплик, риск таймаута | Батчами по PK с commit между; см. ниже |

## CREATE INDEX CONCURRENTLY — нюансы

- Не выполняется внутри транзакционного блока. В Django нужен `atomic = False`; в Alembic —
  `autocommit_block()` или отдельная не-транзакционная ревизия.
- Дольше обычного `CREATE INDEX` и делает два прохода.
- При сбое оставляет **invalid index** — его надо найти (`\d`, `pg_index.indisvalid`) и
  дропнуть (`DROP INDEX CONCURRENTLY`) перед повтором.

## NOT VALID → VALIDATE — паттерн

Двухфазный приём для FK/CHECK/NOT NULL без долгого лока:

```sql
-- Фаза 1: быстро, только новые/изменённые строки проверяются впредь
ALTER TABLE orders ADD CONSTRAINT orders_user_fk
    FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;
-- Фаза 2: сканирует существующие строки под SHARE UPDATE EXCLUSIVE (не блокирует DML)
ALTER TABLE orders VALIDATE CONSTRAINT orders_user_fk;
```

## Backfill больших таблиц

Никогда не обновляй всю таблицу одной транзакцией. Признаки проблемы: `UPDATE` без `WHERE`
по диапазону, data-миграция в транзакции (по умолчанию), отсутствие батчей.

Безопасно — батчами по первичному ключу, с коммитом между батчами, **вне** транзакции миграции,
идемпотентно:

```sql
-- повторять, пока затронуто > 0 строк; между итерациями — commit
UPDATE big_table SET new_col = old_col
WHERE id BETWEEN :lo AND :hi AND new_col IS NULL;
```

Большой backfill лучше вынести из миграции в management-команду/Celery-задачу, чтобы деплой
не висел и его можно было ставить на паузу/возобновлять.

## Таймауты — всегда перед DDL

Чтобы DDL не ждал лок бесконечно, держа очередь к таблице:

```sql
SET lock_timeout = '3s';        -- не ждать лок дольше 3с (упасть и не копить очередь)
SET statement_timeout = '0';    -- но дать самой операции отработать (или разумный лимит)
```

При срабатывании `lock_timeout` миграция упадёт чисто — повторить в момент меньшей нагрузки.
Это предпочтительнее зависшей миграции, заблокировавшей весь трафик к таблице.
