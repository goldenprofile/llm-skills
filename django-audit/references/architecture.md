# Линза: architecture

Архитектурный аудит: структура проекта, модели, views, URLs, шаблоны, формы,
сервисный слой, managers, signals, admin. Префикс находок: `ARC`.

## Чеклист

### Структура проекта
- [ ] Стандартная Django-структура; приложения с осмысленными именами (не app1/myapp)
- [ ] Каждое приложение — одна доменная область; нет «god app» с 50+ моделями
- [ ] Нет циклических зависимостей между приложениями
- [ ] Конфигурация разделена base/dev/prod (для нетривиального проекта)

### Models
- [ ] Модели в `models.py` или пакете `models/`
- [ ] Корректные типы полей; есть `__str__`
- [ ] У ForeignKey/M2M явный `on_delete` и `related_name`
- [ ] Индексы на часто запрашиваемых полях
- [ ] Нет бизнес-логики в моделях (кроме простых свойств)
- [ ] Meta настроен (ordering, verbose_name); абстрактные модели для общих полей (created_at/updated_at)

### Views
- [ ] Тонкие views — логика в сервисном слое, не orchestration-only
- [ ] CBV где уместно; нет прямого SQL в views
- [ ] `get_queryset()` вместо статического `queryset` для динамики
- [ ] Проверяются permissions

### URLs
- [ ] `path()` вместо устаревшего `url()`; осмысленные RESTful-паттерны
- [ ] Namespaces настроены; нет хардкода URL (используется `reverse()`)

### Templates
- [ ] Наследование от base.html; нет логики в шаблонах
- [ ] Статика через `{% static %}`; нет инлайн CSS/JS (или минимум)

### Forms
- [ ] Формы в `forms.py`; ModelForm где возможно
- [ ] Валидация в формах (`clean_*`), не во views

### Сервисный слой
- [ ] Бизнес-логика в `services.py`/`services/`
- [ ] Сервисы не зависят от `request`; тестируемы изолированно
- [ ] Нет «толстых» моделей с бизнес-логикой

### Managers / QuerySets
- [ ] Кастомные managers для сложных запросов; chainable QuerySet-методы
- [ ] Нет `filter()` с магическими строками в views

### Signals
- [ ] Только для decoupling; нет бизнес-логики; зарегистрированы в `apps.py` `ready()`

### Admin
- [ ] Модели зарегистрированы; настроены `list_display`/`search_fields`/`list_filter`
- [ ] Нет чувствительных данных без защиты

## Антипаттерны (Grep)

```python
# Fat views — 100+ строк логики во view-функции
# N+1: цикл по queryset с обращением к related-объекту без select_related/prefetch_related
for post in Post.objects.all():
    print(post.author.name)        # запрос на каждой итерации
# Хардкод URL:
redirect('/users/profile/')        # → reverse('users:profile')
# Бизнес-логика в модели:
class Order(models.Model):
    def process_payment(self): ...  # → в сервис
# Raw SQL без необходимости:
cursor.execute("SELECT ...")
# Прямой импорт settings:
from myproject.settings import DEBUG   # → from django.conf import settings
```

Grep-паттерны: `url\(r'\^`, `ForeignKey\(` без `on_delete`, `redirect\(['"]/`,
`from .*\.settings import`, `cursor\.execute`, `connection\.cursor`, `print\(`,
`TODO|FIXME|HACK`.
