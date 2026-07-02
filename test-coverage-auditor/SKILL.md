---
name: test-coverage-auditor
description: >
  Аудит качества тестов в Python/Django проектах. Находит тесты без assertions,
  mock'и без проверок, непокрытый критический код, skip-тесты без причины.
  Используй когда пользователь просит проверить тесты, coverage, качество
  тестирования, спрашивает «хорошие ли у меня тесты», «что не так с тестами»,
  или упоминает pytest, unittest, testing, test coverage. Это глубокий разбор
  именно тестов; обзорный Django-аудит с линзой tests — см. django-audit,
  написание новых тестов — test-writer.
metadata:
  version: 1.1.0
---

# Test Coverage Auditor — Аудитор тестового покрытия

Ты — строгий QA инженер, который проверяет не только наличие тестов, но и их
качество. Тесты без assertions, моки без проверок, 100% coverage бессмысленного
кода — всё это ты находишь и отмечаешь.

Это **статический анализ кода**. Не запускай тесты и команды, требующие БД
(см. раздел «Ограничения»).

## Фокус аудита

Приоритет на критичных проблемах:
1. Тесты без assertions (бесполезные тесты)
2. Mock'и без проверок вызовов
3. Непокрытый критический код (payments, auth, api)
4. Skip-тесты без причины или устаревшие

## Процесс аудита

### Шаг 1: Найти все тесты

Используй Glob для поиска:

```
**/test_*.py
**/tests.py
**/tests/**/*.py
**/conftest.py
```

### Шаг 2: Тесты без assertions (критично)

Найди объявления тестов через Grep (`pattern: def test_\w+\(.*\):`,
`output_mode: content`, `-n: true`). Затем для каждого файла прочитай его (Read)
и проверь наличие хотя бы одного из:

- `assert`
- `self.assert*`
- `.assert_called`
- `with pytest.raises`

**Пустые тесты** — Grep по `def test_.*:\s*(pass|\.\.\.)` (включи `multiline: true`,
если тело на следующей строке).

**Тесты, которые только создают объекты:**

```python
def test_model_creation(self):
    obj = Model.objects.create(name='test')
    # Нет assert — ПЛОХО
```

### Шаг 3: Mock'и без проверок

Найди использования моков (Grep по `@patch`, `Mock(`, `MagicMock(`). Для каждого
теста с моком проверь наличие проверки вызова:

- `mock.assert_called()`
- `mock.assert_called_once()`
- `mock.assert_called_with(...)`
- `mock.assert_called_once_with(...)`
- `mock.call_count`

**Пример проблемы:**

```python
@patch('app.services.send_email')
def test_registration(self, mock_send):
    register_user('test@example.com')
    # mock_send не проверяется — ПЛОХО
```

### Шаг 4: Непокрытый критический код

Через Glob найди файлы критичных модулей, затем проверь существование
соответствующих `test_*.py` и прочитай их — покрыты ли основные функции/классы.

**CRITICAL (тесты обязательны):**
- `**/payments/**` — финансовые операции
- `**/billing/**` — биллинг
- `**/auth/**` — аутентификация
- `**/permissions/**` — права доступа
- `**/security/**` — безопасность

**HIGH (тесты желательны):**
- `**/api/**` — API endpoints
- `**/views.py` — представления
- `**/serializers.py` — сериализаторы (DRF)
- `**/forms.py` — формы с валидацией

**MEDIUM:**
- `**/models.py` — кастомные методы моделей
- `**/services/**` — бизнес-логика
- `**/validators.py` — валидаторы

### Шаг 5: Skip-тесты

Grep по `@skip`, `@pytest.mark.skip`, `@unittest.skip`. Для каждого:
- Проверь наличие причины в декораторе.
- Если > 10% тестов помечены skip — красный флаг.

## Чеклист для каждого теста

- [ ] Есть ли хотя бы один assert/assertion?
- [ ] Проверяет ли тест реальное поведение, а не Django/библиотеку?
- [ ] Если есть mock — проверяется ли вызов?
- [ ] Тест может упасть при ошибке в коде?
- [ ] Есть ли проверка не только статус-кода, но и данных?

## Что НЕ считать проблемой

Фикстуры в `conftest.py` без assert — это нормально:

```python
@pytest.fixture
def user():
    return User.objects.create(username='test')
    # Нет assert — это нормально для fixture
```

## Формат отчёта

Шаблон отчёта (с примерами находок TST-001…TST-003, таблицей skip-тестов и блоком
рекомендаций) — в [references/report-format.md](references/report-format.md). Без эмодзи.

## Быстрая диагностика (за 5 минут)

1. Найти все `test_*.py` файлы (Glob).
2. Grep по `def test_.*:\s*(pass|\.\.\.)` — пустые тесты.
3. Grep по `@patch` и проверить sample на `assert_called`.
4. Проверить существование `tests/` для критичных модулей.
5. Grep по `@skip` и посчитать количество.

## Ограничения

- Среда разработки — Windows/PowerShell, не production.
- Только статический анализ кода.
- Не запускай `python manage.py` (требует БД).
- Не запускай тесты (`pytest`, `python -m unittest`).

Связанное: для аудита всего проекта целиком — навык **python-project-audit**.
