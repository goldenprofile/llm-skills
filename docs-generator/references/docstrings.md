# Python docstrings — Google-стиль

Docstrings пишем в **Google-стиле** (читаемо, хорошо рендерится в IDE и mkdocstrings).
Принцип тот же: документируем **«почему» и неочевидное**, а не пересказываем сигнатуру. Текст
docstrings — на английском (как принято в коде), даже когда общение с пользователем на русском.

## Что документировать (а что нет)

| Объект           | Документировать                                                        |
|------------------|-----------------------------------------------------------------------|
| **Модуль**       | назначение файла в 1–2 строки, если оно неочевидно из имени            |
| **Публичный класс** | роль, инварианты, как использовать; не перечисляй все атрибуты, если ясны |
| **Публичная функция** | что делает (если неочевидно), побочные эффекты, исключения, тонкости |
| **Сложная логика** | «почему» именно так (комментарий в теле, не docstring)              |

**НЕ документируй:** приватные хелперы (`_helper`) без надобности; тривиальные геттеры/`__init__`,
где всё ясно из сигнатуры; то, что уже сказано type hints (см. ниже).

## Связь с type hints — не дублируй типы

Тип уже в аннотации — **не повторяй его словами**. docstring добавляет смысл, единицы измерения,
ограничения, побочные эффекты, поведение в краевых случаях — то, чего нет в типе.

```python
# ПЛОХО — docstring дублирует type hints, ноль новой информации
def set_timeout(seconds: int) -> None:
    """Set the timeout.

    Args:
        seconds (int): The number of seconds.
    """

# ХОРОШО — добавляет то, чего нет в сигнатуре
def set_timeout(seconds: int) -> None:
    """Set the per-request timeout.

    Applies to all outbound HTTP calls in this session. Values below 1 are
    clamped to 1 to avoid accidental zero-timeout busy loops.

    Raises:
        ValueError: If seconds is negative.
    """
```

Если функция тривиальна и типизирована — docstring может не нужен вовсе. Молчание лучше шума.

## Шаблон функции (Google-style)

```python
def charge_order(order_id: int, amount_cents: int, *, idempotency_key: str) -> Payment:
    """Charge a customer for an order via the payment provider.

    Idempotent: repeated calls with the same idempotency_key return the
    existing Payment instead of charging twice. Network errors are retried
    up to 3 times with backoff before raising.

    Args:
        order_id: ID of the order being paid. Must reference an unpaid order.
        amount_cents: Amount to charge, in minor units (cents) to avoid float math.
        idempotency_key: Caller-generated key; reuse to make retries safe.

    Returns:
        The created or previously-existing Payment.

    Raises:
        OrderNotFound: If order_id does not exist.
        PaymentDeclined: If the provider declines the charge.
    """
```

Секции по необходимости: `Args`, `Returns`, `Yields` (генераторы), `Raises`, `Note`, `Example`.
Не пиши пустые секции. Однострочного описания достаточно для простых функций.

## Класс

```python
class RateLimiter:
    """Token-bucket limiter shared across async handlers.

    Not thread-safe; intended for a single event loop. Refills lazily on
    acquire(), so a long idle period does not accumulate beyond `capacity`.

    Attributes:
        capacity: Max tokens (burst size).
        refill_per_sec: Steady-state rate.
    """
```

Документируй `Attributes` только если они часть публичного контракта и неочевидны.

## Модуль

```python
"""Order analytics aggregation.

Pulls raw orders from Postgres and produces daily/weekly rollups cached in
Redis. Read-only over the orders table; safe to run alongside the web app.
"""
```

## Фреймворк-специфика

```python
# FastAPI — docstring эндпойнта попадает в OpenAPI/Swagger, пиши для потребителя API
@router.get("/orders/{order_id}")
async def get_order(order_id: int) -> OrderOut:
    """Return a single order by ID.

    Returns 404 if the order does not exist or belongs to another user.
    """

# Django — модель: документируй бизнес-смысл и инварианты, не поля (они в самой модели)
class Subscription(models.Model):
    """A user's paid plan. At most one active subscription per user is enforced
    in save(); overlapping date ranges are rejected."""

# aiogram — тонкий handler обычно не нуждается в docstring; документируй service-слой
async def notify_subscribers(bot: Bot, text: str) -> int:
    """Broadcast `text` to all active subscribers, throttled to respect Telegram
    flood limits. Returns the number of messages successfully delivered."""
```

## Анти-паттерны

- Docstring повторяет имя функции: `"""Gets the user."""` для `get_user()` — бесполезно.
- Перечисление каждого аргумента с типом, когда есть аннотации (шум, расходится при рефакторинге).
- Устаревший docstring, описывающий старое поведение — врёт. При правке кода правь docstring.
- Огромный docstring на тривиальной функции — снижает сигнал. Краткость = читаемость.

## Аудит docstrings

- **MEDIUM:** публичная функция/класс/сервис с нетривиальным поведением без docstring; docstring
  описывает поведение, которого в коде уже нет (устарел).
- **LOW:** docstring дублирует type hints; не Google-стиль при принятом в проекте Google-стиле;
  пустые секции `Args:`/`Returns:`.
- Не требуй docstrings на каждом приватном хелпере — это шум, а не качество.
