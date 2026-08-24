# Линза: tests

Аудит качества тестов (не только наличия): тесты без assertions, моки без проверок,
непокрытый критический код, антипаттерны, хрупкость, fixtures, skip/xfail. Префикс: `TST`.
Принцип: качество > количество; высокий coverage без проверок поведения ничего не значит.

Тестовые файлы: `tests.py`, `test_*.py`, `*_test.py`, `tests/` (с `conftest.py` для pytest).

## Пустые / бессмысленные тесты
```python
def test_user_creation(self):
    user = User.objects.create(username='test')   # нет assert
def test_placeholder(self): pass
def test_model(self):
    obj = MyModel.objects.create(name='test'); obj.save()  # ничего не проверяет
```

## Слабые assertions
```python
assert result                  # любой truthy
assert result is not None      # слишком слабо
assert response.status_code == 200   # а тело ответа?
```

## Моки без проверок
```python
@patch('app.services.send_email')
def test_registration(self, mock_send):
    register_user('a@b.com')               # нет mock_send.assert_called_once()
@patch('app.services.external_api')
def test_x(self, mock_api):
    mock_api.return_value = 'ok'
    assert do_something()                  # не проверяет, что mock вызван
```

## Непокрытый критический код
Проверь покрытие для: моделей (кастомные методы, validators, signals); views
(happy path, error cases, permissions, edge cases); сервисов (бизнес-логика,
error handling, границы); API/DRF (endpoints, serializers, permissions).
Особое внимание — payments, auth, api.

## Антипаттерны
```python
def test_django_orm(self):                 # тестирует Django, не наш код
    User.objects.create(username='t'); assert User.objects.filter(username='t').exists()
# зависимость от порядка тестов (общий counter)
requests.get('https://api.external.com')   # реальный внешний запрос в тесте
time.sleep(5)                              # → freezegun/моки
assert not is_expired(datetime(2024,12,31))# hardcoded date — сломается позже
```

## Хрупкие тесты
```python
User.objects.get(id=1)                      # зависимость от конкретного id
items[0].name == 'First'                    # порядок queryset не гарантирован
settings.DEBUG = True                       # мутация глобального состояния
```

## Fixtures / setup
Огромный `setUp` (100 строк, тесты используют 10%); дублирование создания объектов
вместо общих fixtures/conftest.

## Skip / xfail
```python
@pytest.mark.skip                           # без причины
@pytest.mark.skip(reason="TODO: fix later") # висит давно
@pytest.mark.xfail                          # игнорирование известного бага
# >10% тестов в skip — проблема
```

## Ограничение окружения
Покрытие оценивай статически (читая код тестов и сопоставляя с модулями). НЕ запускай
pytest/`manage.py test`. Если нужен точный процент покрытия — отметь как ручной шаг
(`pytest --cov`), а не запускай сам.

В отчёте полезны таблицы: непокрытый критический код (модуль/файл/критичность/покрытие)
и анализ skip/xfail (тест/причина/возраст/действие).
