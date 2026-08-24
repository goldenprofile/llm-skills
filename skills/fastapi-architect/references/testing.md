# Тестирование FastAPI

Главные рычаги: `dependency_overrides` (подмена зависимостей без моков-патчей), отдельная тест-БД,
и async-клиент. Эффект проверяй ассертами (статус + тело + состояние БД), а не «не упало».

## Клиент: AsyncClient (async-стек) или TestClient (просто)

Для async-приложения с async-БД корректнее `httpx.AsyncClient` с `ASGITransport` — он гоняет
запросы по тому же event loop, что и приложение:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_create_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/users", json={"email": "a@b.c", "password": "longpass1"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@b.c"
    assert "password" not in resp.json()        # схема не течёт наружу
```

`TestClient` (на базе того же httpx, синхронный фасад) проще, годится для несложных случаев и
sync-кода: `client = TestClient(app); r = client.get("/users")`. Для тяжёлого async-теста с
реальной async-сессией предпочитай `AsyncClient`.

## dependency_overrides — подмена зависимостей

Главный инструмент изоляции. Подменяй БД-сессию, аутентификацию, внешние клиенты — без monkeypatch.

```python
from app.db import get_session
from app.auth import get_current_user

async def override_get_session():
    async with TestSession() as session:   # сессия на тест-БД
        yield session

def override_current_user():
    return User(id=1, email="test@test", is_admin=False)

app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_current_user
# ...тесты...
app.dependency_overrides.clear()           # обязательно сбросить (лучше в фикстуре)
```

Ключ словаря — **оригинальный объект-зависимость** (`get_session`), значение — замена. Так в
тестах не нужно поднимать реальную аутентификацию или ходить во внешний API.

## Фикстуры и тест-БД

Отдельная БД для тестов (или транзакция с откатом на каждый тест). Схему создавай/сноси в фикстуре:

```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db import get_session
from app.models import Base

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def session():
    engine = create_async_engine("postgresql+asyncpg://.../test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def client(session):
    async def _override():
        yield session
    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

Тест использует `client` — внутри уже подменённая сессия на тест-БД:

```python
@pytest.mark.anyio
async def test_list_users(client, session):
    session.add(User(email="x@y.z", password_hash="..."))
    await session.commit()
    resp = await client.get("/users")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
```

Для async-тестов нужен `anyio` (с `@pytest.mark.anyio` + фикстура `anyio_backend`) или
`pytest-asyncio` (`@pytest.mark.asyncio`). SQLite-in-memory для тест-БД годится только если код не
использует Postgres-специфику; иначе тестируй на postgres (у владельца он есть).

## Что проверять в аудите тестов

- Тесты гоняют реальные ручки через клиент, а не дёргают функции напрямую мимо валидации/DI.
- Зависимости (БД, auth, внешние API) подменены через `dependency_overrides`, а не ходят в прод.
- Проверяется и статус, и тело ответа, и состояние БД — а не только `status_code == 200`.
- Есть негативные кейсы: 401/403 (auth), 422 (валидация Pydantic), 404, конфликт.
- `dependency_overrides` сбрасывается между тестами (иначе протекает состояние).
- Тест-БД изолирована (отдельная база или откат транзакции), тесты не зависят от порядка.
- Качество ассертов и моков без проверок — отдельно прогони навык `test-coverage-auditor`.
