# Линза: celery

Аудит асинхронных задач Celery: конфигурация, определение задач, retry, идемпотентность,
memory leaks, race conditions, chains/groups, Beat, логирование. Префикс находок: `CEL`.

Файлы конфигурации: `celery.py`, `celeryconfig.py`, `settings.py` (`CELERY_*`), `settings/celery.py`.

## Конфигурация

Должно быть настроено (значения — ориентир, подбирай под нагрузку):
```python
CELERY_TASK_SERIALIZER = 'json'          # не pickle
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']         # не ['pickle']
CELERY_TASK_SOFT_TIME_LIMIT = 300        # подбери под задачи
CELERY_TASK_TIME_LIMIT = 600
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1    # для длинных задач
```
Проблемные (Grep):
```python
CELERY_TASK_SERIALIZER = 'pickle'        # RCE-риск
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_ALWAYS_EAGER = True          # синхронное выполнение в prod
CELERY_BROKER_URL = 'redis://localhost:6379'   # localhost в prod
# отсутствие CELERY_TASK_TIME_LIMIT
```

## Определение задач
```python
@shared_task
def my_task(): ...                       # нет bind=True → нет self для retry
@shared_task
def unreliable(): call_external_api()    # нет retry-настроек
@shared_task
def potentially_infinite():
    while True: process()                # нет time limit
@shared_task
def bad(model_instance): ...             # ORM-объект как аргумент → передавать id
```

## Retry
```python
raise self.retry(exc=exc)                # нет countdown (нет backoff)
# лучше: raise self.retry(exc=exc, countdown=2 ** self.request.retries)
@shared_task(bind=True)                   # нет max_retries → бесконечный retry
@shared_task(bind=True, max_retries=None) # тоже бесконечно
```

## Идемпотентность
```python
@shared_task
def charge_user(user_id, amount):
    user.balance -= amount; user.save()  # повтор = двойное списание
# идемпотентно: принять transaction_id и проверить существование перед обработкой
```
Паттерны неидемпотентности: счётчики `+= 1`; `Model.objects.create(...)` без `get_or_create`;
отправка email без дедупликации.

## Memory / ресурсы
```python
all_data = list(Model.objects.all())     # вся таблица в память → .iterator()
# незакрытые соединения внутри задачи
```

## Race conditions
```python
product = Product.objects.get(id=pid)
product.stock -= qty; product.save()      # race
# фикс: with transaction.atomic(): ... select_for_update().get(id=pid)
```

## Chains / Groups / Beat
```python
chain(t1.s(), t2.s(), t3.s())()           # нет обработки ошибок цепочки
group([t.s(i) for i in range(1_000_000)]) # память
chord(group_tasks)(callback)              # нет error callback
# Beat: schedule короче времени выполнения → накопление; нет timezone (app.conf.timezone/enable_utc)
```

## Логирование
- [ ] У задач есть логирование старта/успеха/ошибки (через `logging.getLogger(__name__)`)
- [ ] Бизнес-логика вынесена в сервисный слой, а не «200 строк» внутри задачи

В отчёте полезны таблицы: текущие настройки (параметр/значение/статус) и
по задачам (задача/файл/retry/time_limit/идемпотентность/logging).
