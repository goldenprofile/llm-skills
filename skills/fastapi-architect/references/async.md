# Async-корректность (ключевое)

Самый частый прод-баг FastAPI: блокировка event loop. Один сервер uvicorn в одном процессе крутит
**один** event loop; пока корутина не отдала управление, весь процесс никого не обслуживает.

## Блокировка event loop в async def

В `async def`-роуте нельзя вызывать блокирующий sync-код. Это останавливает обслуживание **всех**
запросов процесса, а не только текущего.

```python
# ОПАСНО: блокирует весь event loop
@router.get("/bad")
async def bad():
    rows = psycopg2_conn.execute(...)   # sync-драйвер БД
    r = requests.get("https://api...")  # sync HTTP
    time.sleep(2)                       # sync-сон
    heavy_cpu_calc()                    # тяжёлый CPU
    return ...
```

Признаки в проде: под нагрузкой растут p99/таймауты у всех ручек, healthcheck отваливается,
хотя CPU не загружен. Чинится одним из способов ниже.

## def vs async def и threadpool

FastAPI обрабатывает их по-разному:

- **`async def`** — выполняется прямо в event loop. Внутри только `await`-аемый async I/O. Любой
  блокирующий вызов здесь — авария.
- **`def`** (обычная функция) — FastAPI уводит её в threadpool (`run_in_threadpool`), event loop
  не блокируется. Это легальный способ для **sync**-кода (sync-драйвер БД, sync-библиотека).

Правило:

```python
# sync-драйвер БД / sync-библиотека → объявляй роут как обычный def
@router.get("/ok-sync")
def ok_sync(db: Session = Depends(get_sync_session)):
    return db.execute(...).all()        # ок: вся ручка в threadpool

# async-драйвер → async def + await
@router.get("/ok-async")
async def ok_async(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User))
    return res.scalars().all()
```

Если уже внутри `async def`, а функция блокирующая — оберни точечно:

```python
from fastapi.concurrency import run_in_threadpool
result = await run_in_threadpool(blocking_sync_call, arg)   # I/O-bound sync
# CPU-bound — лучше отдельный процесс (ProcessPoolExecutor) или внешний воркер
```

threadpool спасает от I/O-блокировки, но не от чистого CPU (GIL): тяжёлый расчёт уводи в процесс
или во внешнюю очередь.

## Async-БД: SQLAlchemy 2.x async + asyncpg

Под async-роуты нужен async-стек: `create_async_engine` (драйвер `postgresql+asyncpg://`),
`async_sessionmaker`, `AsyncSession`, запросы в стиле 2.0 (`select()` + `await session.execute`).

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine("postgresql+asyncpg://...", pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)
```

Сессия — через зависимость с `yield` и закрытием в `finally` (одна сессия на запрос, не глобальная):

```python
async def get_session() -> AsyncSession:
    async with Session() as session:   # __aexit__ закроет сессию
        yield session

@router.get("/users", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).limit(100))
    return res.scalars().all()
```

Ключевое:
- `expire_on_commit=False` — иначе после `commit()` атрибуты «протухают» и их повторное чтение
  вызовет ленивую подгрузку (а в async ленивый I/O вне `await` → ошибка).
- Ленивая загрузка связей в async не работает «сама»: используй явный eager-load
  (`selectinload(User.posts)`), иначе словишь `MissingGreenlet`/ошибку доступа.
- Объект сессии **не глобальный и не общий между запросами** — это data race и порча транзакций.

Анти-паттерн: одна `AsyncSession`/`Session` создана на старте и переиспользуется всеми запросами.

## BackgroundTasks vs внешняя очередь

`BackgroundTasks` — для коротких побочных действий **после** ответа (отправить письмо, записать
лог), выполняется в том же процессе.

```python
@router.post("/signup")
async def signup(data: UserCreate, bg: BackgroundTasks, svc: UserService = Depends()):
    user = await svc.create(data)
    bg.add_task(send_welcome_email, user.email)   # быстро, не критично
    return {"ok": True}
```

Не годится для: тяжёлой/долгой работы, того, что нельзя терять при рестарте, ретраев. Это уйдёт
во внешнюю очередь (у владельца есть redis: RQ/Celery/arq/dramatiq). Помни: sync-таск в
`BackgroundTasks` тоже уйдёт в threadpool, а блокирующий async-таск заблокирует loop.

## Таймауты и конкурентность

- На внешние вызовы — всегда таймаут: `httpx.AsyncClient(timeout=10.0)`; для БД — таймауты на
  пуле/запросе. Без таймаута зависший апстрим держит соединение и исчерпывает пул.
- Параллельные независимые async-вызовы — через `asyncio.gather`, а не последовательно:
  `a, b = await asyncio.gather(fetch_a(), fetch_b())`.
- Один `httpx.AsyncClient` на приложение (в `lifespan` → `app.state`), а не новый на каждый запрос
  (новый клиент = новый пул соединений каждый раз).
