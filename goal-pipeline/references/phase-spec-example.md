# Пример: спека фазы + готовая строка `/goal`

Сквозной мини-пример для brownfield-задачи: *«вынести расчёт скидок из вьюхи в
сервисный слой и покрыть тестами»* в Django-проекте. Профиль — checkpoint-on-risky.

---

## `.goalrun/STATE.md` (живой прогресс)

```markdown
# Goal Pipeline — STATE

Status: READY_TO_DISPATCH
Profile: checkpoint-on-risky
Baseline ref: a1b9c4e
Current phase: 1
Total phases: 3

## События
- 2026-06-25 — план утверждён, pre-flight green (ruff, pyright, pytest)
```

---

## `.goalrun/phases/phase-1.md` (safety-net, не risky)

```
GP_PHASE_START
Phase: 1 of 3 — Add characterization tests
Risky: no
Mandatory commands: pytest -q tests/test_discounts.py, ruff check ., pyright
Gates: test-coverage-auditor
Acceptance criteria: 5
Evidence required: pytest output (exit 0), список новых тестов, coverage по discounts
Depends on: none

## Задача
Зафиксировать текущее поведение расчёта скидок ДО рефакторинга. Тесты пишутся
против существующей вьюхи `orders/views.py::checkout`, без изменения продакшен-кода.

## Критерии приёмки (yes/no)
- [ ] Файл `tests/test_discounts.py` существует и содержит ≥ 5 кейсов
- [ ] Покрыты: нулевая скидка, процентная, фиксированная, стэк двух скидок, скидка > суммы (clamp)
- [ ] `pytest -q tests/test_discounts.py` → exit 0, все тесты зелёные
- [ ] Каждый тест имеет реальный assert на итоговую сумму (не только отсутствие исключения)
- [ ] Продакшен-код orders/ не изменён (дифф против baseline = только tests/)

## Evidence
Вывод pytest (последние 10 строк + exit code), `git diff --stat <baseline>` показывает
только tests/, отчёт test-coverage-auditor.
```

---

## `.goalrun/phases/phase-2.md` (рефакторинг, не risky)

```
GP_PHASE_START
Phase: 2 of 3 — Extract discount service
Risky: no
Mandatory commands: pytest -q, ruff check ., pyright
Gates: /code-review
Acceptance criteria: 6
Evidence required: pytest output, дифф orders/services/discounts.py, результат /code-review
Depends on: 1

## Задача
Вынести логику скидок из `checkout` в `orders/services/discounts.py::apply_discounts`.
Вьюха вызывает сервис. Поведение неизменно — характеризующие тесты фазы 1 остаются
зелёными без правок.

## Критерии приёмки (yes/no)
- [ ] `orders/services/discounts.py::apply_discounts(order) -> Decimal` существует
- [ ] `orders/views.py::checkout` вызывает сервис, не содержит арифметики скидок
- [ ] Все тесты фазы 1 проходят без изменений (поведение сохранено)
- [ ] `pytest -q` → exit 0 (полный набор)
- [ ] `pyright` без новых ошибок; `ruff check .` чисто
- [ ] /code-review по диффу фазы — без findings уровня high
```

> Если бы фаза трогала `**/migrations/**`, поле было бы `Risky: yes` и
> `Gates: migration-safety-auditor` — исполнитель напечатал бы `GP_HALT` перед ней.

---

## `.goalrun/phases/phase-3.md` (Polish & Harden, финал)

```
GP_PHASE_START
Phase: 3 of 3 — Polish & harden discounts
Risky: no
Mandatory commands: pytest -q, ruff check ., pyright
Gates: /code-review (весь дифф прогона)
Acceptance criteria: 5
Evidence required: pytest, обработка edge cases, итоговый /code-review

## Задача
Edge cases и чистота: отрицательная сумма заказа, None-скидка, конкурентный стэк,
логирование решения о скидке. Финальный sweep по всему диффу прогона.

## Критерии приёмки (yes/no)
- [ ] Отрицательная/нулевая сумма заказа обрабатывается явно (тест есть)
- [ ] Нет debug-print / TODO, добавленных за прогон (cleanliness-grep чист)
- [ ] Полный `pytest -q` зелёный, coverage по orders/services/ ≥ исходного
- [ ] /code-review по всему диффу прогона — без high findings
- [ ] Docstring у `apply_discounts` описывает правила стэка скидок
```

---

## Готовая строка `/goal` (этап 7 печатает её)

````
```
/goal "Первым действием прочитай .goalrun/PROTOCOL.md и исполняй строго по нему, начиная с Current phase из .goalrun/STATE.md; фазы со статусом done не переисполняй. Done when: напечатан GP_RUN_COMPLETE, перед ним GP_AUDIT и по одному GP_PHASE_DONE на каждую фазу из .goalrun/ROADMAP.md, а после GP_AUDIT в транскрипте виден фактический вывод переrun'а mandatory-команд с кодом выхода 0 у каждой; ИЛИ напечатан GP_HALT, содержащий номер фазы, проваленный критерий (или причину чекпоинта) и предложение следующего шага; ИЛИ число ходов достигло 24."
```
````

Условие держит только точку входа и done-предикат: сама процедура живёт в
`PROTOCOL.md`, поэтому обновление протокола не требует переписывать строку и
два источника не разъезжаются.

Done-предикат намеренно не сводится к матчу маркеров: `GP_RUN_COMPLETE` можно
напечатать, не запустив ни одной команды, поэтому условие требует ещё и
**фактический вывод** переrun'а с кодом 0 — это оценщик читает в транскрипте.
Ветка `GP_HALT` тоже не бесплатная: halt без номера фазы, причины и следующего
шага условию не удовлетворяет, иначе «напечатай GP_HALT» стал бы дешёвым
способом закрыть цель при любом затруднении.
