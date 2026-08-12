# Архитектура и структура (aiogram 3.x)

Чистая структура снижает баги и упрощает тесты. Здесь — идиомы 3.x и типовые анти-паттерны.

## Router вместо одного Dispatcher

В 3.x хендлеры вешаются на `Router`, роутеры включаются в `Dispatcher`:

```python
# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
router = Router()

@router.message(CommandStart())
async def start(message): ...

# __main__.py
dp = Dispatcher(storage=storage)
dp.include_router(start.router)
dp.include_router(checkout.router)
```

Анти-паттерн: всё в одном файле на `@dp.message(...)`. Дроби по доменам (start, menu, checkout),
каждый — свой роутер. Порядок включения = порядок проверки; более специфичные фильтры выше.

## Фильтры — magic `F` и встроенные

```python
from aiogram import F
from aiogram.filters import Command, StateFilter

@router.message(Command("help"))
@router.callback_query(F.data == "open_menu")
@router.message(F.text.regexp(r"^\d+$"))
```

Не разбирай `message.text` вручную через `if/elif` там, где есть фильтр — фильтры декларативны
и тестируемы.

## Middlewares — outer vs inner

```python
router.message.middleware(SomeMiddleware())         # inner: после фильтров, только если хендлер найден
router.message.outer_middleware(SomeMiddleware())   # outer: до фильтров, на каждый апдейт
```

- **outer** — для того, что нужно на каждом апдейте до роутинга: throttling, бан-чек, логирование.
- **inner** — для контекста конкретного хендлера: подгрузка пользователя из БД, i18n.
- Передавай зависимости через `data` (см. DI). Не делай тяжёлый блокирующий I/O в middleware
  без необходимости — он на каждом апдейте.

## DI — зависимости через workflow_data / middleware

Не создавай глобальные синглтоны и не лезь в модульные переменные. Прокидывай зависимости:

```python
# через run_polling — попадут в kwargs хендлеров
dp.run_polling(bot, db=db_pool, settings=settings)

# или через middleware
class DBMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        data["user"] = await get_user(data["db"], event.from_user.id)
        return await handler(event, data)

@router.message()
async def h(message, db, user): ...   # db/user приходят из workflow_data/middleware
```

## FSM и storage

```python
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

class Order(StatesGroup):
    waiting_address = State()

@router.message(Order.waiting_address)
async def got_address(message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.clear()
```

- **Storage**: `MemoryStorage` — только dev (теряется при рестарте). Прод — `RedisStorage`
  (см. deploy.md). Конфигурируется на `Dispatcher(storage=...)`.
- Не храни большие объёкты/секреты в FSM-данных; это сериализуется в storage.
- Всегда предусматривай выход из состояния (отмена, таймаут логики), иначе пользователь
  «залипает» в шаге.

## Bot и параметры по умолчанию (3.7+)

```python
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
```

`Bot(token, parse_mode=...)` — устаревший способ (deprecated с 3.7). Проверь, как создаётся `Bot`.

## Вынос бизнес-логики из хендлеров (ключ к тестам)

Хендлер должен быть тонким: распарсил апдейт → вызвал сервис → ответил. Бизнес-логику держи в
отдельных функциях/сервисах, не завязанных на `Message`/`Bot`. Тогда логику можно юнит-тестировать
без Telegram (см. testing.md), а хендлеры — точечно.

Анти-паттерн: вся логика (БД, расчёты, внешние вызовы) прямо в теле хендлера — нетестируемо и
блокирует event loop.

## Типовая структура проекта

```
bot/
├── __main__.py        # сборка Bot/Dispatcher, include_router, startup/shutdown, run_polling
├── config.py          # настройки из env (pydantic-settings), токен НЕ в коде
├── handlers/          # роутеры по доменам
├── keyboards/         # сборка клавиатур
├── middlewares/       # throttling, DB, i18n
├── services/          # бизнес-логика (тестируемая, без aiogram-типов)
├── states.py          # StatesGroup
└── db/                # модели, репозитории (async)
```
