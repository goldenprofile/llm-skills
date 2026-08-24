---
name: postgres-performance
description: >
  Запрос или ручка тормозит — найти причину в БД и устранить: чтение EXPLAIN
  ANALYZE, подбор индекса (btree, GIN, partial, covering), поиск медленных
  запросов (pg_stat_statements), пул соединений (pgbouncer против пула
  драйвера), autovacuum и bloat, память под типовой VPS. Django и
  SQLAlchemy. Используй когда пользователь говорит «посмотри, можно ли
  оптимизировать бекенд <url>», «запрос тормозит», «база медленная», просит
  подобрать индекс или прочитать план, упоминает EXPLAIN,
  pg_stat_statements, slow query. Безопасность создания индекса на живой
  таблице — migration-safety-auditor; N+1 на уровне ORM — django-audit.
metadata:
  version: 1.2.0
---

# Postgres Performance

Диагностика «почему медленно» и тюнинг PostgreSQL для Python-бэкенда на VPS.
Порядок всегда один: **сначала найти виновника измерением, потом лечить** — не
предлагай индексы и настройки вслепую.

## Когда применять

- Конкретный запрос/страница тормозит, нужен разбор плана и индекс.
- «БД в целом медленная» — нужен поиск топ-запросов.
- Настройка pgbouncer, памяти, autovacuum под размер VPS.

## Контекст — установить ПЕРВЫМ делом

1. **Версия PG, размер БД, ресурсы VPS** (`SELECT version();`,
   `pg_database_size`, RAM/CPU сервера).
2. **ORM и доступ** — Django ORM / SQLAlchemy; есть ли доступ к psql на проде.
   Диагностические команды — **read-only, выполняются на сервере** (у владельца
   локальной БД нет); любые изменения схемы/конфига — отдельным явным шагом.
3. **Симптом** — один запрос, одна страница, «всё», пики по времени суток?

## Процесс

### 1. Найти виновника

- `pg_stat_statements` (включить, если нет — требует рестарта, предупреди):
  топ по `total_exec_time` и по `mean_exec_time`.
- Альтернатива без расширения: `log_min_duration_statement = 500` (мс) →
  медленные запросы в лог.
- На dev: django-debug-toolbar / silk — увидеть, какие SQL порождает страница
  (N+1 отдаёт django-audit, здесь — сами запросы).

### 2. Прочитать план: `EXPLAIN (ANALYZE, BUFFERS) <query>`

Красные флаги (по убыванию частоты):

| В плане | Значит | Лечение |
|---|---|---|
| `Seq Scan` на большой таблице + узкий фильтр | нет подходящего индекса | индекс по колонкам фильтра |
| `rows=1000000` estimate vs `actual rows=10` | устаревшая статистика | `ANALYZE table;`, поднять `default_statistics_target` для колонки |
| `Sort Method: external merge Disk` | сортировка не влезла в память | `work_mem` для сессии/запроса, индекс под ORDER BY |
| `Nested Loop` с большим внешним набором | плохой выбор join-плана | индекс по join-колонке, проверить статистику |
| `Filter: ... Rows Removed by Filter: <огромное>` | индекс есть, но не тот | составной/partial индекс под реальный предикат |
| Высокие `Buffers: read` при повторных прогонах | данные не в кеше | `shared_buffers` / `effective_cache_size`, охлаждение bloat |

### 3. Индексы — правила проектирования

- **Селективность:** индекс окупается на колонках, отсекающих большинство строк;
  на `boolean`-колонке сам по себе почти бесполезен → partial:
  `CREATE INDEX ... WHERE status = 'pending'`.
- **Составной:** порядок колонок = равенство → диапазон
  (`(user_id, created_at)` для `WHERE user_id = ? AND created_at > ?`);
  левый префикс работает, правый — нет.
- **Covering:** `INCLUDE (col)` — чтобы получить Index Only Scan без похода в кучу.
- **GIN** — для `JSONB` (`@>`), массивов, полнотекста (`tsvector`), `pg_trgm`
  для `ILIKE '%...%'`.
- Каждый индекс замедляет запись и ест место — не вешай «на всякий случай»;
  неиспользуемые ищи в `pg_stat_user_indexes` (`idx_scan = 0`).
- **Создание на проде — только `CREATE INDEX CONCURRENTLY`**; в Django это
  `AddIndexConcurrently` + `atomic = False` — прогони миграцию через
  `migration-safety-auditor`.

### 4. Серверные настройки (типовой VPS, ориентиры)

- `shared_buffers` = 25% RAM; `effective_cache_size` = 50–75% RAM.
- `work_mem` — осторожно: умножается на число сортировок × соединений;
  для отдельного тяжёлого запроса — `SET LOCAL work_mem = '64MB'`.
- `maintenance_work_mem` повыше на время создания индексов.
- Менять по одному параметру, замерять до/после одинаковым запросом.

### 5. Соединения и пулинг

- Симптом `too many connections` / `FATAL: remaining connection slots`:
  сначала выясни, кто держит (`pg_stat_activity`, `state = 'idle'`).
- Django: `CONN_MAX_AGE` (персистентные соединения) — достаточно для одного
  сервиса; pgbouncer (transaction mode) — когда воркеров/сервисов много.
  В transaction mode недоступны session-фичи: `SET`, advisory locks,
  prepared statements (для Django — `server_side_binding` осторожно).
- SQLAlchemy: `pool_size`/`max_overflow` соизмеряй с `max_connections`.

### 6. Autovacuum и bloat

- Раздутая таблица при малом числе живых строк:
  `pg_stat_user_tables` (`n_dead_tup`), расширение `pgstattuple` для точной оценки.
- Не выключай autovacuum; для горячих таблиц — понизь
  `autovacuum_vacuum_scale_factor` per-table.
- `VACUUM FULL` блокирует таблицу целиком — на проде только в окно, чаще
  достаточно обычного `VACUUM (ANALYZE)`.

## Уровни риска рекомендаций

- **Read-only диагностика** (EXPLAIN, pg_stat_*) — безопасно всегда.
- **Индекс CONCURRENTLY, ANALYZE** — безопасно, но нагружает I/O: не в пик.
- **Правка postgresql.conf, pgbouncer, VACUUM FULL** — требует рестарта/окна:
  явно предупреждай и давай план отката.

## Быстрый чеклист

- [ ] Виновник найден измерением (pg_stat_statements / лог), не догадкой.
- [ ] План прочитан: estimate ≈ actual, нет Seq Scan по большим таблицам без причины.
- [ ] Индекс: селективный, порядок колонок обоснован, создание CONCURRENTLY.
- [ ] Настройки меняются по одной, эффект замерен тем же запросом.
- [ ] Неиспользуемые индексы проверены перед добавлением новых.

## Связь с библиотекой навыков

- `migration-safety-auditor` — обязательный гейт на миграцию с новым
  индексом/constraint.
- `django-audit` — N+1 и ORM-паттерны (select_related/prefetch_related);
  сюда приходи, когда SQL уже правильный, но медленный.
- `vps-ops` — базовая настройка postgres на VPS (пользователи,
  бэкапы); здесь — производительность поверх неё.
- `ratchet-loop` — «снизить время запроса/число запросов» как метрика храповика.
