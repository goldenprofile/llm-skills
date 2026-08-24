# Django migrations — специфика

Общие риски операций — в [postgres-operations.md](postgres-operations.md). Здесь — как они
проявляются в Django и как переписывать безопасно.

## Смотреть реальный SQL

Django скрывает SQL за операциями. Перед вердиктом смотри, что реально уйдёт в БД:

```bash
python manage.py sqlmigrate app_label 0042      # SQL конкретной миграции
python manage.py makemigrations --check --dry-run # CI: упасть, если миграция не создана
python manage.py showmigrations                   # что не применено
```

## `atomic = False`

По умолчанию каждая миграция на Postgres оборачивается в транзакцию. Это **обязательно**
отключать для:

- `CREATE INDEX CONCURRENTLY` (нельзя в транзакции);
- батч-backfill (нужны промежуточные коммиты).

```python
class Migration(migrations.Migration):
    atomic = False
    operations = [...]
```

Минус `atomic=False`: при сбое посреди миграции она применится частично — пиши операции
идемпотентно и порядком, допускающим повторный запуск.

## Индексы без блокировки

Не `migrations.AddIndex`, а concurrent-вариант из `django.contrib.postgres`:

```python
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False
    operations = [
        AddIndexConcurrently("order", models.Index(fields=["user_id"], name="order_user_idx")),
    ]
```

`RemoveIndexConcurrently` — симметрично.

## Добавление полей

- **Новое `NOT NULL`-поле**: Django предложит one-off default и впишет его в `UPDATE` всех
  строк → на большой таблице это CRITICAL. Безопасно: добавить `null=True` → backfill
  батчами (отдельная `RunPython`-миграция с `atomic=False`) → отдельной миграцией снять
  `null` через паттерн `NOT VALID`/`VALIDATE` (часто проще `SeparateDatabaseAndState` +
  ручной `RunSQL`).
- На старых PG (≤10) Django при добавлении поля с default ставил `DEFAULT` и тут же снимал —
  это вызывало rewrite. На PG 11+ для константного default rewrite нет.

## `RunPython` — обратимость и транзакции

- Всегда передавай `reverse_code`. Если откат бессмысленен — явно `migrations.RunPython.noop`,
  а не пропуск (иначе миграция необратима, что повышает риск до MEDIUM).
- Внутри `RunPython` используй `apps.get_model("app", "Model")` (historical model), а не
  прямой импорт — иначе миграция сломается при будущих изменениях модели.
- Для backfill: `atomic=False` на миграции + батчи + `.iterator()`/срезы по PK, не `.all()`.

```python
def forwards(apps, schema_editor):
    Order = apps.get_model("shop", "Order")
    qs = Order.objects.filter(total__isnull=True)
    # батчами по PK, а не один UPDATE на всю таблицу
    ...

operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
```

## Rename без поломки — `SeparateDatabaseAndState`

`RenameField`/`RenameModel` мгновенно ломают старый код при rolling-деплое. Чтобы изменить
*состояние* Django без DDL (или наоборот, выполнить DDL вручную безопасным способом):

```python
operations = [
    migrations.SeparateDatabaseAndState(
        state_operations=[migrations.RenameField("order", "amount", "total")],
        database_operations=[],  # БД не трогаем; колонку переключаем через expand/contract
    )
]
```

## Прочее

- **Не редактируй применённые на проде миграции** — расхождение с `django_migrations`.
  Для чистки истории — `squashmigrations` (и только после того, как старые применены везде).
- **Разделяй схему и данные**: schema-операции и `RunPython`-backfill — в разных миграциях
  (разные требования к `atomic`, разный риск, раздельный откат).
- **SQLite**: см. [deploy-models.md](deploy-models.md). Django эмулирует сложный `ALTER`
  через пересоздание таблицы (table rebuild) — медленно и блокирует; на больших данных в
  SQLite это сигнал, что пора на Postgres.
