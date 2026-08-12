# Линза: legacy

Поиск технического долга: deprecated зависимости и Django-импорты, забытый legacy,
конфигурационный legacy, файловые артефакты, незавершённые рефакторинги. Префикс: `LEG`.

Файлы зависимостей: `requirements.txt`, `requirements/*.txt`, `Pipfile(.lock)`, `pyproject.toml`.

## Deprecated пакеты (Django-экосистема)
Флагать (список — ориентир, сверяйся с актуальным состоянием экосистемы на момент аудита):
```
django-celery        → django-celery-beat + django-celery-results
django-nose          → pytest-django
mock                 → unittest.mock (встроен с Python 3.3)
six, future          → не нужны для Python 3-only
boto                 → boto3
PIL                  → Pillow
pycrypto             → pycryptodome
psycopg2 (без -binary) → psycopg2-binary или psycopg 3
celery < 5.0, kombu < 5.0, factory-boy < 3.0, django-cors-headers < 3.0
```
Также проверяй EOL-версии самого Django (есть ли известные CVE, не вышла ли из поддержки).

## Deprecated Django-импорты/методы (Grep)
```python
from django.utils.encoding import smart_text            # → smart_str
from django.utils.translation import ugettext           # → gettext
from django.conf.urls import url                         # → django.urls.path
from django.core.urlresolvers import reverse             # → django.urls.reverse
from django.utils import six                             # удалён в Django 3.0
from django.utils.encoding import python_2_unicode_compatible  # удалён
from django.db.models import NullBooleanField            # → BooleanField(null=True)
from django.contrib.postgres.fields import JSONField     # → django.db.models.JSONField
PASSWORD_RESET_TIMEOUT_DAYS                              # → PASSWORD_RESET_TIMEOUT (секунды)
request.is_ajax()                                        # удалён в Django 3.1+
QuerySet.extra()                                         # → annotate/aggregate
```

## Забытый legacy (Grep)
Комментарии-маркеры: `TODO FIXME HACK XXX DEPRECATED LEGACY TEMP TEMPORARY REMOVE`,
`OLD CODE`, `WORKAROUND`, рус. «старый/устарел/удалить/временно/хак».
Мёртвые ветки: закомментированный код (>3 строк), `if False:`/`if 0:`, код после `return`, `except: pass`.

## Конфигурационный legacy
```python
ENABLE_OLD_FEATURE = False; USE_LEGACY_SYSTEM = True
DEPRECATED_* = ; OLD_* = ; LEGACY_* =
CELERY_BROKER_URL = ...; BROKER_URL = ...     # дублирование старого/нового имени
```

## Файловый legacy
`*.bak *.backup *.old *.orig *_old.py *_backup.py *_deprecated.py old_* backup_* deprecated_*`;
`__pycache__/` в git; `*.sqlite3` если prod на PostgreSQL.
Директории: `/old/ /backup/ /deprecated/ /legacy/ /temp/`.

## Незавершённые рефакторинги
```python
class OldUserService / class NewUserService / class UserServiceV2
# версионирование в именах: _v1 _v2 _old _new _legacy _deprecated
```

В отчёте полезна таблица зависимостей: пакет / текущая / последняя / статус / приоритет,
и оценка сложности миграции (breaking changes).
