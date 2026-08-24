# Структура проекта и сборка приложения (FastAPI)

Цель — тонкие роуты, изолированный сервисный слой, явная конфигурация и предсказуемый старт/стоп.

## APIRouter — дробление по доменам

Не вешай все ручки на один `app`. Каждый домен — свой `APIRouter`, который подключается в `app`:

```python
# app/users/router.py
from fastapi import APIRouter, Depends
from app.users import schemas, service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=schemas.UserRead, status_code=201)
async def create_user(data: schemas.UserCreate, svc: service.UserService = Depends()):
    return await svc.create(data)

# app/main.py
from fastapi import FastAPI
from app.users.router import router as users_router

app = FastAPI()
app.include_router(users_router)
```

`prefix` и `tags` задаются на роутере, а не повторяются в каждой ручке. Версионирование API —
через префикс (`APIRouter(prefix="/api/v1")`) или вложенный роутер, см. также OpenAPI ниже.

## lifespan вместо on_event

Актуальный способ управлять ресурсами на старте/остановке — `lifespan` (async context manager).
`@app.on_event("startup"/"shutdown")` устарели.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: создаём пул БД, redis, http-клиент
    engine = create_async_engine(settings.db_url, pool_pre_ping=True)
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.http = httpx.AsyncClient(timeout=10.0)
    yield
    # shutdown: закрываем ресурсы
    await app.state.http.aclose()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

Ресурсы — в `app.state`, доступ из ручек через `Depends`, а не через глобальные переменные модуля.
`engine.dispose()` на shutdown обязателен, иначе соединения утекают при рестарте под systemd.

## Настройки через pydantic-settings

Конфиг — из env, типизированный, не разбросанный по `os.getenv`. (В Pydantic v2 `BaseSettings`
вынесен в отдельный пакет `pydantic-settings`.)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")
    db_url: str
    redis_url: str
    secret_key: str
    debug: bool = False

settings = Settings()  # упадёт на старте, если обязательная переменная не задана — это хорошо
```

Секреты (`secret_key`, пароль БД) — только из env / `EnvironmentFile` systemd, не в репозитории.

## Тонкие роуты + сервисный слой

Роут должен: распарсить вход (Pydantic-схема), вызвать сервис, вернуть результат. Бизнес-логика,
работа с БД и внешними API — в сервисе, не завязанном на `Request`/`Response`.

```python
# app/users/service.py
class UserService:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create(self, data: UserCreate) -> User:
        user = User(email=data.email, password_hash=hash_pw(data.password))
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
```

`Depends()` без аргумента для класса-сервиса работает: FastAPI вызовет `UserService(...)`,
разрешив его собственные зависимости (`get_session`). Сервис тестируется без поднятия HTTP.

Анти-паттерн: запросы к БД и расчёты прямо в теле ручки — нетестируемо, плюс легко случайно
заблокировать event loop (см. `async.md`).

## Типовая структура

```
app/
├── main.py            # FastAPI(...), lifespan, include_router, exception handlers
├── config.py          # Settings (pydantic-settings), секреты из env
├── db.py              # engine, async_sessionmaker, get_session() (зависимость с yield)
├── errors.py          # обработчики исключений, единый формат ошибки
├── users/
│   ├── router.py      # APIRouter (тонкие ручки)
│   ├── service.py     # бизнес-логика (тестируемая)
│   ├── schemas.py     # Pydantic-схемы запрос/ответ
│   └── models.py      # ORM-модели (SQLAlchemy)
└── tests/
    ├── conftest.py    # фикстуры: app, AsyncClient, тест-сессия, dependency_overrides
    └── test_users.py
```

ORM-модели (`models.py`) и API-схемы (`schemas.py`) — **разные файлы и разные классы**; почему —
см. `pydantic.md`. Зависимость `get_session` живёт в `db.py` и переопределяется в тестах.
