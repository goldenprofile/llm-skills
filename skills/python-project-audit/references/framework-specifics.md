# Адаптация под фреймворки

Дополнительные проверки в зависимости от фреймворка.

## FastAPI

- Используются ли `Depends` для DI
- Pydantic-модели на всех эндпоинтах (request/response)
- Async-совместимость (нет blocking I/O в `async def`)
- Lifespan events вместо deprecated `on_event`
- BackgroundTasks vs Celery — правильный выбор

## Django

- Нет логики во views (толстые модели vs сервисный слой)
- `select_related` / `prefetch_related`
- Django REST Framework — сериализаторы, permissions
- Миграции — нет конфликтов, нет data-миграций без reverse
- Settings разделены по окружениям
- `ALLOWED_HOSTS`, `SECURE_*` настройки

## Flask

- Application factory pattern
- Blueprints для модульности
- Flask-SQLAlchemy — правильное управление сессиями
- Нет глобального состояния
- Расширения актуальны и поддерживаются
