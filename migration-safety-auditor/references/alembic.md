# Alembic / SQLAlchemy — специфика

Общие риски операций — в [postgres-operations.md](postgres-operations.md). Здесь — ловушки
Alembic при FastAPI/SQLAlchemy-стеке.

## `autogenerate` не ловит всё — ревьюить обязательно

`alembic revision --autogenerate` удобно, но опасно. Чего он **не** видит или видит неверно:

- **Переименования** колонок/таблиц — генерирует `drop_column` + `add_column`, то есть
  **молчаливую потерю данных**. Всегда заменяй на `op.alter_column(..., new_column_name=...)`
  вручную.
- Часть изменений типов, `server_default`, `CHECK`-constraint, имена индексов/constraint
  (зависит от настройки `compare_type`/`compare_server_default` и naming convention).
- Любые data-изменения и backfill — не его задача.

Всегда читай сгенерированный `upgrade()`/`downgrade()` перед применением. Смотри offline-SQL:

```bash
alembic upgrade <rev> --sql        # SQL без применения
alembic history / alembic current  # что и где применено
```

## CONCURRENTLY и операции вне транзакции

Alembic по умолчанию оборачивает миграцию в транзакцию. Для `CREATE INDEX CONCURRENTLY` и
батч-backfill нужен autocommit:

```python
def upgrade():
    with op.get_context().autocommit_block():
        op.create_index(
            "order_user_idx", "order", ["user_id"],
            postgresql_concurrently=True, if_not_exists=True,
        )
```

Альтернатива — отключить транзакцию на миграцию через `transaction_per_migration` /
кастомный `env.py`. При сбое concurrent-индекс остаётся invalid — дропнуть и повторить.

## `NOT VALID` → `VALIDATE` через `op.execute`

Для FK/CHECK/NOT NULL на больших таблицах — двухфазно сырым SQL:

```python
def upgrade():
    op.execute("ALTER TABLE orders ADD CONSTRAINT orders_user_fk "
               "FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID")
    with op.get_context().autocommit_block():
        op.execute("ALTER TABLE orders VALIDATE CONSTRAINT orders_user_fk")
```

## `downgrade()` — реальный или честно нереализуемый

- Пустой `downgrade()` или `pass` = необратимая миграция (MEDIUM-риск). Либо реализуй откат,
  либо `raise NotImplementedError("необратимо: данные не восстановить")` — явный отказ лучше
  тихой пустоты.
- `autogenerate` нередко генерирует кривой `downgrade()` — проверяй симметрию руками.

## SQLite — `batch_alter_table`

SQLite почти не поддерживает `ALTER` (нельзя сменить тип, многие constraint). Alembic
эмулирует через move-and-copy (создать новую таблицу → скопировать → удалить → переименовать):

```python
def upgrade():
    with op.batch_alter_table("user") as batch:
        batch.alter_column("age", type_=sa.Integer())
```

Это пересоздаёт таблицу — медленно и блокирующе на больших данных, а SQLite допускает лишь
одного писателя. Признак, что проект перерос SQLite — см. [deploy-models.md](deploy-models.md).

## `server_default` vs `default`

Python-side `default=` в модели **не** пишется в схему БД и не заполняет существующие строки.
Чтобы значение появилось на уровне БД и для старых строк — нужен `server_default=` и/или
явный backfill.
