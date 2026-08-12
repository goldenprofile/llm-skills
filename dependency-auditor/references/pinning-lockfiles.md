# Пиннинг, lockfiles и воспроизводимые установки

Цель — чтобы «то, что прошло тесты» и «то, что встало на прод» было **байт-в-байт** одним
набором версий, включая транзитивные. Это достигается двумя слоями: *манифест* (что хочу,
с диапазонами) и *lockfile* (что именно поставится, точные версии + хеши).

## Манифест vs lockfile — разделение ролей

- **Манифест** (`pyproject.toml [project.dependencies]`, `requirements.in`) — намерения:
  прямые зависимости с разумными диапазонами (`django>=5.0,<6.0`). Редактируешь руками.
- **Lockfile** (`uv.lock`, `poetry.lock`, скомпилированный `requirements.txt`) — резолв:
  точные версии всего дерева + хеши. Генерируется инструментом, **коммитится в git**,
  руками не правится.

Антипаттерн: единственный `requirements.txt` с диапазонами (`django>=5.0`) как «и манифест,
и lock». Установка невоспроизводима — завтра приедет другая minor/patch.

## Стратегии пиннинга

| Где | Как пинить | Почему |
|-----|-----------|--------|
| Прямые прод-зависимости (манифест) | Диапазон по semver: `>=X.Y,<X+1` (caps на мажор) | Получаешь патчи безопасности, но не ловишь мажорные breaking changes автоматически |
| Весь граф (lockfile) | Точные версии `==` + хеши | Воспроизводимость и защита от подмены |
| Транзитивная с CVE, родитель отстаёт | Прямой пин/constraint `>=fixed` | Закрыть уязвимость, не дожидаясь родителя |
| Приложение (не библиотека) | Можно жёстче: `==` и в манифесте | Деплой одной известной версии |
| Библиотека (публикуешь в PyPI) | Широкие диапазоны, **не** коммить lock в дистрибутив | Не навязывать версии потребителям |

Голый `*`, `latest`, отсутствие верхней границы у критичных пакетов → невоспроизводимость и
риск внезапного мажора. Слишком жёсткий `==` во всех прямых зависимостях приложения — допустимо,
но тогда патчи безопасности приходится бампать руками; компромисс — `==` в lock, диапазон в манифесте.

## uv

```bash
uv add "django>=5.0,<6.0"        # добавить прод-зависимость в pyproject + обновить uv.lock
uv add --dev pytest ruff          # dev-группа (в [dependency-groups]/[tool.uv])
uv lock                           # пересобрать uv.lock из pyproject
uv lock --upgrade                 # пересчитать lock, подняв всё в рамках диапазонов
uv lock --upgrade-package django  # поднять только один пакет
uv sync                           # привести venv в точное соответствие uv.lock
uv sync --frozen                  # установить строго по lock, НЕ трогая/не пересобирая его (CI/прод)
uv sync --locked                  # как frozen: упасть, если lock устарел относительно pyproject
uv export --format requirements-txt --no-dev -o requirements.txt   # экспорт с хешами для не-uv окружений
```

`uv.lock` содержит хеши и кросс-платформенный резолв. На проде/в CI — `uv sync --frozen`
(или `--locked`), чтобы установка не «уплыла».

## Poetry

```bash
poetry add "django@^5.0"          # прод-зависимость (^5.0 = >=5.0,<6.0)
poetry add --group dev pytest     # dev-группа [tool.poetry.group.dev.dependencies]
poetry lock                       # пересобрать poetry.lock
poetry lock --no-update           # пересобрать lock БЕЗ подъёма версий (после ручной правки pyproject)
poetry update                     # поднять всё в рамках ограничений + обновить lock
poetry update django              # поднять только один пакет
poetry install --sync             # привести окружение в соответствие lock (удалит лишнее)
poetry install --without dev      # прод-установка без dev-группы
poetry export -f requirements.txt --without-hashes -o requirements.txt  # экспорт (плагин poetry-plugin-export)
```

`poetry.lock` хранит хеши (`[[package]].files`). Коммить его. На проде — `poetry install`
(без `--no-root`/с учётом проекта) ставит ровно версии из lock.

## pip + pip-tools (компиляция requirements)

Классический воспроизводимый стек на чистом pip: `requirements.in` (намерения) →
`pip-compile` → `requirements.txt` (lock с хешами).

```bash
pip install pip-tools
pip-compile --generate-hashes requirements.in -o requirements.txt   # lock с хешами
pip-compile --generate-hashes requirements-dev.in -o requirements-dev.txt
pip-compile --upgrade requirements.in                                # поднять всё
pip-compile --upgrade-package django requirements.in                 # поднять один пакет
pip-sync requirements.txt requirements-dev.txt                       # привести venv в соответствие

# Воспроизводимая установка с проверкой хешей:
pip install --require-hashes -r requirements.txt
```

`--require-hashes` заставляет pip проверять хеш каждого артефакта — главный приём против
подмены пакета (typosquat/MITM). Требует, чтобы **все** строки имели хеши (что и даёт
`pip-compile --generate-hashes`).

## Хеши — зачем

Хеш фиксирует не только версию, но и сам артефакт (wheel/sdist). Без хешей злоумышленник,
получивший контроль над индексом/зеркалом, может подменить файл той же версии. С хешами —
установка упадёт. Все три стека умеют хеши: uv.lock и poetry.lock — по умолчанию, pip — через
`--generate-hashes` + `--require-hashes`.

## Разделение prod / dev

Уязвимость в линтере или тестране — это **не** прод-риск; смешение раздувает прод-образ и
поверхность атаки. Разделяй:

- **uv**: `[dependency-groups]` (`dev`), ставить прод как `uv sync --no-dev`.
- **poetry**: `[tool.poetry.group.dev.dependencies]`, прод — `poetry install --without dev`.
- **pip-tools**: отдельные `requirements.in` и `requirements-dev.in` (dev `-c` на prod lock).
- **plain pip**: `requirements.txt` + `requirements-dev.txt`.

В отчёте: dev/test-зависимости с CVE → понижай риск (см. `scanning.md`); неразделённые
prod/dev → MEDIUM.

## Воспроизводимость — чеклист

- [ ] Lockfile существует и **закоммичен** в git.
- [ ] Lockfile содержит **хеши**.
- [ ] Прод/CI устанавливает строго из lock (`uv sync --frozen` / `poetry install` /
      `pip install --require-hashes`), а не `pip install` по диапазонам.
- [ ] Манифест и lockfile синхронны (`uv sync --locked` / `poetry lock --no-update` чисто проходит).
- [ ] Prod и dev-зависимости разделены.
- [ ] Зафиксирована версия Python (`requires-python` / `.python-version`) — резолв от неё зависит.
