# Goal Pipeline — протокол исполнителя

Этот файл планировщик копирует в `.goalrun/PROTOCOL.md` (этап 4): исполнитель —
свежая `/goal`-сессия без контекста планировщика, протокол должен лежать на диске.

## Цикл исполнителя (внутри одной `/goal`-сессии)

Цикл до `GP_RUN_COMPLETE` или `GP_HALT`:

1. Прочитай `.goalrun/STATE.md` → `Current phase: N`, `Profile`.
2. **Чекпоинт-проверка.** Если профиль `per-phase`, ИЛИ профиль `checkpoint-on-risky`
   и фаза N помечена `Risky: yes` — напечатай `GP_HALT` (что за фаза, почему risky,
   что будет сделано) и **остановись, не начиная фазу**. Управление возвращается
   пользователю; он ре-диспатчит ту же строку `/goal` как подтверждение.
3. Прочитай `.goalrun/phases/phase-N.md` → полная спека.
4. Напечатай `GP_PHASE_START` (поля из спеки).
5. Сделай работу. Прогони mandatory-команды (последние ~10 строк + код выхода в
   транскрипт). Вызови вшитые гейты по спеке (через Skill-инструмент).
6. Напечатай `GP_PHASE_VERIFY`: каждый критерий `pass|fail` + evidence;
   build/type/lint/test; результат каждого гейта; cleanliness (новые `print(`/
   `console.log`/debug, session TODO/FIXME, мёртвые импорты — grep по диффу против
   baseline ref). Любой провал → 3-strike (см. ниже).
7. **Memory writeback.** Узнал что-то неочевидное, полезное будущему прогону?
   Запиши memory-файл в memory-каталог (frontmatter `name`/`description`/
   `metadata.type`), залинкуй из `MEMORY.md`, напечатай `MEMORY_SAVED: <name>`.
   Иначе `MEMORY_SAVED: none`. Никогда не сохраняй секреты/эфемерное.
8. Напечатай `GP_PHASE_DONE`; обнови `STATE.md` (фаза N done, `Current phase: N+1`,
   строка события).
9. Пришло новое сообщение пользователя? Пауза на границе фазы, разберись, спроси
   перед продолжением.
10. N < total → к шагу 1. N == total → **финальный аудит**, потом `GP_RUN_COMPLETE`.

## 3-strike восстановление

- **1-й провал критерия:** `FAILURE_PROBE` (что упало, что пробовал, гипотеза
  корня) → авто-ретрай той же фазы один раз с probe как фидбек. Не продвигаться.
- **2-й провал:** `FAILURE_ESCALATE` → фокус-fix-спека `phase-N.fix.md` (только
  падающий критерий, без scope creep) → исполни инлайн → пере-VERIFY → при pass
  идём на N+1.
- **3-й провал:** `GP_HALT` с историей трёх попыток и предложением следующего шага;
  `STATE.md → Status: BLOCKED`; остановись. Пользователь берёт руль.

## Финальный аудит (один проход, до 2 раундов fix)

Per-phase VERIFY — самоотчёты; поздняя фаза могла молча сломать раннюю. Аудит
перепроверяет против **исходного** `ROADMAP.md`:

1. `GP_AUDIT_START` (раунд, число фаз, критериев, дедуп-набор команд).
2. Перечитай `ROADMAP.md` — критерии из исходного плана, не из VERIFY.
3. Completeness: по одному `GP_PHASE_DONE` на каждую фазу 1..N.
4. Переrun дедуп-набор mandatory-команд (build/type/lint/полный test). Ненулевой
   код выхода → gap.
5. Deliverable-чек: для каждого deliverable-файла из ROADMAP проверь наличие в
   рабочем дереве против baseline ref (committed+staged+unstaged, плюс untracked).
   `missing` → gap.
6. Spot-check проверяемых критериев («файл X есть», «функция Y экспортирована») —
   через `ls`/`grep`/`cat`. Недетерминируемые («скриншот показал X») → `trust-prior`.
7. `GP_AUDIT` с per-phase статусом, кодами команд, критериями pass/fail/trust-prior,
   deliverables present/missing.
   - Есть дыры → `GP_AUDIT_GAPS`, фокус-fix-спека `audit-fix-<round>.md`, исполнить
     инлайн, раунд+1. На 3-м провале → `GP_HALT`, `STATE.md → BLOCKED`.
   - Чисто → `GP_RUN_COMPLETE` с 5-строчным резюме. Если доля `trust-prior` > 30% —
     баннер «⚠ Audit coverage: X re-verified, Y trust-prior. Глазами проверь UI до мержа».

## Прерывание

Любое сообщение пользователя по ходу → пауза на границе фазы (после
`GP_PHASE_DONE`, до чтения следующей спеки), разобраться, спросить перед
продолжением. Правка следующей фазы → обнови `phase-N.md`, попроси ре-диспатч.

## Маркеры транскрипта (минимальный набор)

Оценщик `/goal` видит **только транскрипт** — маркеры обязаны быть в выводе агента,
не просто в файлах.

| Маркер | Когда |
|---|---|
| `GP_PHASE_START` / `GP_PHASE_VERIFY` / `GP_PHASE_DONE` | по разу на фазу |
| `MEMORY_SAVED: <name\|none>` | между VERIFY и DONE |
| `FAILURE_PROBE` / `FAILURE_ESCALATE` | 1-й / 2-й провал критерия |
| `GP_HALT` | чекпоинт risky-фазы, per-phase стоп, или 3-strike блок — **возврат управления** |
| `GP_AUDIT_START` / `GP_AUDIT` / `GP_AUDIT_GAPS` | финальный аудит |
| `GP_RUN_COMPLETE` | финал, после `GP_AUDIT` |

Условие `/goal`: **done when `GP_RUN_COMPLETE` напечатан, ИЛИ `GP_HALT` напечатан**
(остановка возвращает управление; пользователь ре-диспатчит ту же строку).

## Память (Windows)

Memory-каталог бери из того, что харнесс показывает в начале сессии (путь зависит
от проекта/cwd — обычно `…\.claude\projects\<slug>\memory`). Формат файла —
твой стандартный: frontmatter `name` / `description` / `metadata.type`
(`feedback`/`project`/`reference`/`user`), тело с фактом, линки `[[name]]`,
строка-указатель в `MEMORY.md`. На финальной фазе всегда пиши `project_<slug>.md`
(локация, стек, статус, ссылка на ROADMAP) — чтобы будущий прогон стартовал умнее.
