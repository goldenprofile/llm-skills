# Тестирование ботов (aiogram 3.x)

У aiogram нет «официального» тест-клиента уровня FastAPI TestClient. Рабочие подходы — ниже.
Главный принцип: **бизнес-логику тестируй отдельно от Telegram**, хендлеры — точечно.

## 1. Вынеси логику из хендлеров — и тестируй её обычным pytest

Если бизнес-логика в `services/` и не зависит от `Message`/`Bot`, она тестируется без aiogram:

```python
# services/pricing.py
def total(items): ...

# tests/test_pricing.py
def test_total():
    assert total([...]) == 100
```

Это покрывает большую часть рисков без моков Telegram и согласуется с навыком
`test-coverage-auditor` (тесты с реальными assertion, без пустых моков).

## 2. Тест хендлера через мок Bot и `feed_update`

Для самих хендлеров — прогоняй апдейт через диспетчер с замоканным `Bot` (его сетевые вызовы
не должны ходить в Telegram):

```python
import pytest
from unittest.mock import AsyncMock
from aiogram import Dispatcher
from aiogram.types import Update, Message, Chat, User
from aiogram.fsm.storage.memory import MemoryStorage

@pytest.fixture
def bot():
    b = AsyncMock()                      # send_message и пр. — корутины-моки
    b.id = 42
    return b

@pytest.fixture
def dp():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    return dp

@pytest.mark.asyncio
async def test_start_replies(dp, bot):
    msg = Message(message_id=1, date=..., chat=Chat(id=1, type="private"),
                  from_user=User(id=1, is_bot=False, first_name="A"), text="/start")
    await dp.feed_update(bot, Update(update_id=1, message=msg))
    bot.send_message.assert_awaited()    # хендлер действительно ответил
```

Ключевое — проверять **эффект** (что вызвано `send_message`/изменён state), а не просто «не упало».

## 3. Тест переходов FSM

С `MemoryStorage` прогоняй последовательность апдейтов и проверяй состояние/данные:

```python
@pytest.mark.asyncio
async def test_order_flow(dp, bot):
    await dp.feed_update(bot, _msg("/order"))
    await dp.feed_update(bot, _msg("ул. Пушкина"))
    # проверь, что состояние очищено и данные сохранены через сервис/репозиторий
```

Используй `StorageKey(bot_id, chat_id, user_id)` чтобы прочитать state/data из storage в тестах.

## 4. Сторонние помощники

Есть community-библиотеки (например, `aiogram_tests`) с готовыми `MockedBot`/реквест-хендлерами.
Удобно, но проверь совместимость с твоей версией aiogram 3.x — API быстро меняется. Базовый
подход с `AsyncMock` + `feed_update` работает без зависимостей.

## Что проверять в аудите тестов бота

- Есть ли тесты вообще на хендлеры и на переходы FSM (а не только на утилиты).
- Бизнес-логика вынесена и покрыта (или всё в хендлерах → почти нетестируемо).
- Тесты проверяют эффект (`assert_awaited`/изменение state), а не просто отсутствие исключения.
- Сетевые вызовы Telegram замоканы — тесты не ходят в реальный API.
- Негативные сценарии: заблокированный пользователь, неверный ввод в FSM, флуд-ошибка.
