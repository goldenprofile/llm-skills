# Пример контракта и прогона ratchet-loop

Конкретный brownfield-пример: снижение числа SQL-запросов на странице каталога
Django-портала. Показывает заполненный `RL_CONTRACT`, заморозку оценщика, формат
`results.tsv` и финал.

---

## RL_CONTRACT (этап 1)

```
RL_CONTRACT
Артефакт (мутируемая цель): apps/catalog/views.py  (только этот файл)
Замороженный оценщик:       python tools/bench_catalog.py
Якорь метрики:              ^queries:
Метрика / направление:      queries (число SQL на рендер страницы) / minimize
Epsilon:                    0  (счётчик запросов детерминирован, дрожания нет)
Бюджет на попытку:          120s wall-clock
Условие останова:           plateau:8  (8 попыток подряд без улучшения)
Профиль автономности:       checkpoint-on-verify, K=5
Baseline ref:               a1b2c3d
Из памяти:                  prefetch_related для tags уже пробовали в ratchet_catalog.md — не помог, пропустить
```

`tools/bench_catalog.py` поднимает тестовый клиент, рендерит страницу под
`CaptureQueriesContext` и печатает `queries: <N>`. Он **не импортирует** ничего из
`apps/catalog/views.py` как источник истины о «правильном» числе — иначе цель могла
бы подсунуть ответ.

## RL_EVAL_LOCKED (этап 2)

```
RL_EVAL_LOCKED
frozen-set:
  tools/bench_catalog.py        7f3a9c1
  tools/fixtures/catalog.json   2b8e004
Пересечение с целью: пусто ✓
```

## results.tsv (этап 4)

```
trial	commit	metric	status	eval_ok	description
0	a1b2c3d	83	keep	yes	baseline
1	b2c3d4e	51	keep	yes	select_related для brand/category
2	c3d4e5f	51	discard	yes	prefetch tags (в пределах epsilon, сложнее) — откат
3	d4e5f6g	0	crash	yes	only() обрезал поле, шаблон упал — откат
4	e5f6g7h	39	keep	yes	Prefetch с queryset для images (active=True)
5	f6g7h8i	39	discard	yes	annotate count вместо .count() в цикле — равно, сложнее
6	g7h8i9j	31	keep	yes	values_list для id-списка фильтра
```

Заметь строки 2 и 5: метрика равна, но код сложнее → **discard** по критерию
простоты. Строка 3 — crash (откат). `eval_ok=yes` везде — хеши frozen-set держатся.

## RL_VERIFY (этап 5, чекпоинт после 5 keep-ов)

```
RL_VERIFY (checkpoint)
1. Целостность оценщика:   хеши == EVAL.lock ✓
2. Воспроизводимость:      чистый чекаут g7h8i9j → queries: 31 (== best) ✓
3. Анти-хак скан диффа:    нет хардкода/чтения фикстуры/глушения исключений ✓
4. Сайд-эффекты:           дифф только в apps/catalog/views.py ✓
Вердикт: PASS
```

## RL_RUN_COMPLETE (этап 6)

```
RL_RUN_COMPLETE
Метрика: 83 → 31 запрос (−63%)
Попытки: 7 (keep 4 / discard 2 / crash 1)
Сработало: select_related для FK, Prefetch с фильтрованным queryset, values_list для id
Лог: .ratchetrun/results.tsv
Запас: похоже на плато — дальше пагинация/кеш, но это смена контракта (другой артефакт)
MEMORY_SAVED: ratchet_catalog_views
```

---

## Опциональная обёртка под `/goal` (необязательно)

Ядро ratchet-loop host-agnostic и по умолчанию крутится in-session. Для unattended
прогона можно обернуть в `/goal` с **плато-условием** (только так у `/goal`
появляется терминальное условие; keep-or-revert всё равно живёт в протоколе
исполнителя, оценщик его не делает):

```
/goal "Крути ratchet-loop по контракту .ratchetrun/CONTRACT.md: каждая попытка —
правка только мутируемой цели, прогон замороженного оценщика, keep при улучшении
сверх epsilon иначе git reset, строка в results.tsv, RL_VERIFY каждые K keep-ов.
Сверяй хеши frozen-set перед каждой попыткой; расхождение → RL_HALT. Done when
plateau:8 достигнуто и финальный RL_VERIFY зелёный (RL_RUN_COMPLETE), ИЛИ напечатан
RL_HALT."
```

Дефолт — без `/goal`: меньше движущихся частей, а per-trial `git reset` и так живёт
в сессии.
