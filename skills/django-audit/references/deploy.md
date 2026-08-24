# Линза: deploy

Валидация готовности к production: settings, security headers, БД, кэш, email, статика,
зависимости, миграции, логирование, error tracking, Celery, Docker, .env, CI/CD,
healthcheck, документация. Префикс: `DEP`. Вердикт: NOT READY / CONDITIONAL / READY.
Блокируй деплой при CRITICAL.

Примечание: security-settings частично пересекаются с линзой `security` (A05). Здесь —
с акцентом на prod-готовность; при полном аудите дублируй находку только один раз.

## Settings
```python
# MUST в production:
DEBUG = False
ALLOWED_HOSTS = ['конкретные.домены']        # не ['*'] и не []
SECRET_KEY = os.environ['SECRET_KEY']        # из env
# ИСКАТЬ: DEBUG=True, ALLOWED_HOSTS=['*'], SECRET_KEY='django-insecure-*' или хардкод
# Security headers:
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000               # значение под политику проекта
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## Database / Cache / Email / Static
```python
'ENGINE': 'django.db.backends.postgresql'    # не sqlite3 в prod
'PASSWORD': ''                               # пустой пароль — плохо
'CONN_MAX_AGE': 60                           # пуллинг
# Cache: НЕ locmem/dummy в prod
# Email: НЕ console/filebased backend в prod
STATIC_ROOT = BASE_DIR / 'staticfiles'       # для collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # если не CDN
```

## Dependencies
- Версии закреплены (`pkg==1.2.3`, не `>=`/без версии)
- Нет dev-зависимостей в prod; есть gunicorn/uvicorn (не runserver); whitenoise (если не CDN); sentry-sdk (рекомендуется)
- Разделение `requirements/{base,dev,prod}.txt`

## Миграции (статически)
Все миграции в git; нет конфликтов. Динамические проверки (`showmigrations`,
`makemigrations --check`) — НЕ запускать; отметить как ручной шаг для пользователя.

## Logging / Error tracking
```python
'level': 'WARNING'                           # не DEBUG в prod
# рекомендуется Sentry: sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], environment='production')
```

## Celery
```python
CELERY_BROKER_URL = 'redis://localhost:6379' # хардкод localhost
CELERY_ALWAYS_EAGER = True                    # синхронно
```

## Docker / .env
- Multi-stage build; non-root user; нет secrets в build args; `.dockerignore`; healthcheck
- ИСКАТЬ: `COPY . .` (тянет .git/.env), `USER root`
- `.env` в `.gitignore`; есть `.env.example` без реальных значений; нет `.env` в репозитории (CRITICAL если есть)

## CI/CD
Запуск тестов; linting (ruff/flake8); security checks (bandit, safety).

## Healthcheck / docs
Endpoint `/health/` с проверкой БД; README с запуском, список env-переменных,
инструкции по миграциям, rollback-процедура.

В отчёте полезен блок «Environment Variables (требуемые)» и чеклист по секциям
Settings / Infrastructure / Monitoring.
