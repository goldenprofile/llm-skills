# Линза: cleanup

Поиск мусора: мёртвый код, неиспользуемые импорты, недостижимый код, TODO/FIXME,
закомментированный код, дубли, пустые конструкции, файловый мусор, проблемы миграций,
пустые тесты, забытые print. Префикс находок: `CLN`. Только находи и рекомендуй — не удаляй сам.

## Мёртвый код
```python
import os                                  # не используется
from django.shortcuts import render, redirect   # redirect не используется
def helper_old(): ...                       # нигде не вызывается
class UnusedMixin: ...                       # никто не наследует
def func():
    return result
    cleanup()                               # недостижимо после return
if False: do_something()                     # всегда False
if condition: pass
else: do_real_work()                         # пустая ветка
```

## TODO/FIXME археология
Категории: `TODO` (план), `FIXME` (баг), `HACK` (костыль), `XXX` (внимание).
Для каждого: возраст (git blame), автор, актуальность, блокирует ли что-то.

## Закомментированный код
Блоки закомментированного кода (>3 строк) → удалить, он есть в git history.

## Дублирование
Copy-paste функции с минимальными отличиями → вынести общее.

## Пустые/бессмысленные конструкции
```python
class EmptyClass: pass                       # если не Enum/Exception
try: risky()
except: pass                                 # молча глотает ошибки
if True: ...                                 # бессмысленная проверка
if cond: return True
else: return False                           # лишний else после return
```

## Файловый мусор
`file_copy.py`/`file_backup.py`; `*.pyc`, `__pycache__/`, `.coverage`, `*.log` в git;
конфиги неиспользуемых инструментов (`.travis.yml` при GitHub Actions).

## Миграции
```python
operations = []                              # пустая миграция
# >20 миграций в app → кандидат на squash
migrations.RunPython(forward, migrations.RunPython.noop)  # без reverse
```

## Тесты (пересекается с линзой tests — здесь только «мусорный» аспект)
```python
def test_x(self): pass                       # пустой
def test_y(self): ...                         # заглушка
def test_z(self): result = f()               # нет assert
@skip
def test_broken(self): pass                   # skip без причины
```

## Логирование / print
```python
print("debug"); print(f"value: {value}")     # забытый debug
# logger.debug("here")                        # закомментированные логи
# избыточный logger.debug на каждую строку
```

## Автоматизация (рекомендации пользователю, не запускать сам)
```bash
autoflake --in-place --remove-all-unused-imports -r .
isort .
vulture .
```
Замечание: «мёртвый» код иногда нужен (абстрактные методы, точки расширения) — учитывай контекст.
