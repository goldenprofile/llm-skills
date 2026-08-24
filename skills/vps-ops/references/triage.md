# Режим triage — прод сломался

Систематический поиск причины на Linux VPS (systemd + nginx + postgres + redis).
Пользователь выполняет команды на сервере и присылает вывод; ты ведёшь
диагностику и интерпретируешь.

## Золотое правило

**Собери улики ДО перезапуска.** `systemctl restart` уничтожает состояние
процесса; если сервис жив после рестарта — причина осталась неизвестной и
вернётся. Рестарт — осознанное решение после сбора, или когда простой дороже
диагноза (тогда собери минимум: status + последние логи + dmesg).

## Контекст — установить ПЕРВЫМ делом

1. **Симптом** — что видно снаружи: 502/504/timeout/бот молчит/всё лежит.
2. **Что менялось** — был ли деплой/миграция/обновление пакетов перед началом
   (`git log -3` на сервере, `journalctl --since "-2h" -u app`).
3. **Масштаб** — один сервис или всё (если SSH тоже еле живой — смотри ресурсы
   в первую очередь).

## Быстрая триада (всегда первой, ~1 минута)

```bash
systemctl status app --no-pager -l      # состояние, последний код выхода
journalctl -u app -n 100 --no-pager     # последние логи сервиса
df -h; free -h; uptime                  # диск, память, load average
```

Дальше — по дереву симптомов.

## Дерево диагностики

### Сервис упал / рестарт-луп

- `systemctl status`: `Result: exit-code` + код → ищи последний traceback в
  `journalctl -u app -n 200`; `Result: oom-kill` или `dmesg -T | grep -i oom` →
  память (ниже); `Result: watchdog` → сервис завис, не падал.
- Луп после деплоя → почти всегда код/окружение: несовместимая миграция,
  отсутствующая переменная в EnvironmentFile, невыполненный `pip install`.
  Проверка: запусти команду из `ExecStart=` вручную под пользователем сервиса.
- `status=203/EXEC` — путь/права в ExecStart; `status=1` сразу — смотри первые
  строки трейсбека, не последние.

### nginx 502 Bad Gateway

Бэкенд мёртв или недоступен nginx'у:
- `systemctl status app` — жив ли gunicorn/uvicorn вообще.
- `tail -50 /var/log/nginx/error.log` — `connect() failed`: к какому
  сокету/порту; сверь с реальным (`ss -tlnp | grep <port>` или права на unix-сокет).
- Живой процесс + 502 = слушает не там, где ждёт nginx (типично после смены
  конфига одного из двух).

### nginx 504 Gateway Timeout

Бэкенд жив, но не успевает:
- Долгий запрос: длинная вьюха, внешний API без таймаута, медленный SQL
  (`pg_stat_activity` → `state='active'` дольше минуты → `postgres-performance`).
- Все воркеры заняты: gunicorn с N воркерами и одним зависшим апстримом
  выедается мгновенно — ищи внешний вызов без таймаута.
- `proxy_read_timeout` в nginx против реального времени ответа.

### Диск заполнен (df 100%)

- Виновник: `du -xh / --max-depth=2 2>/dev/null | sort -rh | head -15`.
  Типовые: journald (`journalctl --disk-usage` → `--vacuum-size=500M`),
  логи в /var/log без ротации, postgres WAL (не удалять руками! — искать
  причину: отвалившаяся репликация/archive_command), /tmp, старые бэкапы.
- После освобождения: postgres мог перейти в read-only по факту ENOSPC —
  проверь `journalctl -u postgresql` и запись в БД.
- Inodes: `df -i` (место есть, файлы не создаются).

### Память / CPU 100%

- `top` (по %MEM / %CPU): кто. OOM-killer уже приходил? `dmesg -T | grep -i oom`
  — жертва не всегда виновник (OOM убивает большого, а течь может другой).
- Течёт воркер gunicorn → `max_requests` + `max_requests_jitter` как митигейшн,
  причину искать профилированием (не в инциденте).
- Swap занят при свободной RAM — не паника; swap in/out постоянный (`vmstat 1`) —
  реальная нехватка.

### Postgres не принимает соединения

- `too many connections` → `pg_stat_activity`: кто держит; массовый `idle` —
  утечка пула у приложения (CONN_MAX_AGE/pool_size), «долгие active» —
  зависшие запросы (`pg_terminate_backend` точечно).
- Сервис лежит: `systemctl status postgresql`, `journalctl -u postgresql -n 50` —
  частая причина: диск (см. выше) или OOM.
- `pg_isready -h 127.0.0.1` — отделить «постгрес лежит» от «сеть/права».

### Бот молчит (aiogram)

- `systemctl status bot` + логи: `TelegramConflictError` (409) → второй
  polling-инстанс (старый процесс не убит, дубль на другом сервере, вебхук
  не снят: `getWebhookInfo`).
- Ошибок нет, апдейтов нет → сеть до api.telegram.org (`curl -s
  https://api.telegram.org` с сервера), либо бот забанен/токен сменён.
- Детальный разбор паттернов — `aiogram-bot-auditor`.

## Чеклист «собрать до рестарта»

- [ ] `systemctl status <svc>` (полностью, с Result и кодом выхода)
- [ ] `journalctl -u <svc> -n 200 --no-pager`
- [ ] `dmesg -T | tail -50` (OOM, диски, сеть)
- [ ] `df -h && df -i && free -h && uptime`
- [ ] Что менялось: `git log --oneline -5`, время последнего деплоя
- [ ] Для веба: `tail -50 /var/log/nginx/error.log`

## Куда дальше

- Причина в медленных запросах, а не в падении → `postgres-performance`.
- Инцидент заметили пользователи раньше тебя → режим **observe**
  ([references/observability.md](observability.md)): какой слой поймал бы.
- Дыра в конфиге (нет `Restart=`, лимитов, ротации) → режим **deploy** в SKILL.md.
