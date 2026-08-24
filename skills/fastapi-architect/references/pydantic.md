# Pydantic v2: модели, схемы, валидаторы, response_model

Всё ниже — Pydantic **v2** API. Сначала определи версию (см. ловушки миграции в конце).

## Модели vs схемы: разделяй

ORM-модель (SQLAlchemy) описывает таблицу; API-схема описывает контракт HTTP. Это **разные классы**.
Один класс на оба назначения течёт: наружу уходят `password_hash`, внутренние поля, а вход
принимает то, что клиент задавать не должен (`id`, `is_admin`).

Делай отдельные схемы под вход и выход:

```python
from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):           # вход: только то, что шлёт клиент
    email: EmailStr
    password: str

class UserRead(BaseModel):             # выход: только безопасные поля
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    # password_hash НЕ перечислен — наружу не попадёт
```

`from_attributes=True` (бывший v1 `orm_mode`) позволяет собрать схему из ORM-объекта по атрибутам:
`UserRead.model_validate(user_orm)`. FastAPI делает это автоматически при `response_model=UserRead`.

## response_model — контракт ответа

Указывай `response_model` (или возвращай схему как тип) — тогда FastAPI отфильтрует ответ по схеме,
даже если из сервиса вернулась ORM-модель с лишними полями. Это и контракт, и защита от утечки.

```python
@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, svc: UserService = Depends()):
    return await svc.get(user_id)   # вернёт ORM User, наружу уйдёт только UserRead-поля
```

Полезные параметры: `response_model_exclude_none=True`, `status_code=201`. Для частичного
обновления (PATCH) — отдельная схема с `Optional`-полями и `model_dump(exclude_unset=True)`.

## model_config

Конфиг модели — через `model_config = ConfigDict(...)` (в v1 был вложенный `class Config`):

```python
from pydantic import BaseModel, ConfigDict

class Item(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,   # сборка из ORM/атрибутов
        extra="forbid",         # запретить лишние поля во входе (вместо тихого игнора)
        str_strip_whitespace=True,
    )
```

`extra="forbid"` на входных схемах ловит опечатки клиента и устаревшие поля вместо молчаливого
проглатывания.

## Валидаторы: field_validator и model_validator

Поле-валидатор (в v1 — `@validator`):

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password too short")
        return v
```

`mode="before"` — валидатор получает сырой вход до приведения типа (нормализация); `mode="after"`
(по умолчанию) — после. Кросс-полевую логику делай через `model_validator`:

```python
from pydantic import BaseModel, model_validator

class SignUp(BaseModel):
    password: str
    password_repeat: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_repeat:
            raise ValueError("passwords do not match")
        return self
```

`@model_validator(mode="after")` работает с экземпляром (`self`), возвращает `self`.
`@field_validator` обязательно с `@classmethod` под декоратором.

## Сериализация

- `model_dump()` → dict (в v1 был `.dict()`); `model_dump_json()` → JSON-строка.
- `model_validate(obj)` → из dict/атрибутов (в v1 — `parse_obj`/`from_orm`).
- Управление выводом: `model_dump(exclude_none=True, exclude_unset=True, by_alias=True)`.
- Кастомная сериализация поля — `@field_serializer`; вычисляемое поле — `@computed_field`.

## Типичные ловушки миграции v1 → v2

| v1 | v2 |
|----|----|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `@validator("x")` | `@field_validator("x")` + `@classmethod` |
| `@root_validator` | `@model_validator(mode="before"/"after")` |
| `.dict()` / `.json()` | `.model_dump()` / `.model_dump_json()` |
| `parse_obj()` / `from_orm()` | `.model_validate()` |
| `Config.allow_population_by_field_name` | `ConfigDict(populate_by_name=True)` |
| `BaseSettings` из `pydantic` | пакет `pydantic-settings` (`pip install`) |
| `Field(..., regex=)` | `Field(..., pattern=)` |
| `info.config`/`field` в валидаторе как аргументы | через `info: ValidationInfo` |

Проверь, что в проекте не осталось v1-вызовов после апгрейда — они либо упадут, либо работают
через deprecated-шим и сломаются на следующей мажорной версии.
