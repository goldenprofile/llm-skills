# Безопасность хоста: least privilege для одиночного VPS

Соло-разработчик, один VPS, прямой доступ к интернету. Базовый периметр: не-root сервис,
firewall, секреты вне репозитория, защищённый SSH. Без этого остальное неважно.

## Не-root сервисный пользователь

Каждое приложение — под своим системным пользователем, не под root и не под личным аккаунтом:

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin appuser
chown -R appuser:appuser /opt/myapp
```

- `nologin` — под этим пользователем нельзя залогиниться интерактивно.
- Компрометация приложения под root = компрометация всего хоста (CRITICAL). Под `appuser`
  — ограничена правами пользователя.
- В юните: `User=appuser`. Усиление через systemd-sandboxing (`ProtectSystem=strict`,
  `NoNewPrivileges`, `ReadWritePaths`) — см. systemd.md.

## Секреты в EnvironmentFile, НЕ в репозитории

```bash
# /opt/myapp/.env  — права и владелец
chown appuser:appuser /opt/myapp/.env
chmod 600 /opt/myapp/.env            # читать может только владелец
```

- `.env` в `.gitignore`; в репо — только `.env.example` без значений.
- В unit — `EnvironmentFile=/opt/myapp/.env`, а не `Environment=SECRET=...` (последнее видно
  в `systemctl show`).
- Секрет в git-истории = утечка даже после удаления: ротируй (новый пароль БД, новый `SECRET_KEY`,
  отзыв токена бота у @BotFather). Удаление файла из HEAD не чистит историю.
- `DJANGO_SECRET_KEY`, `DATABASE_URL`, `BOT_TOKEN`, `REDIS_URL`, ключи внешних API — только в env.

## Firewall (ufw)

Запрещаем всё входящее, открываем точечно:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp        # SSH (или твой кастомный порт)
ufw allow 80/tcp        # HTTP (редирект на HTTPS)
ufw allow 443/tcp       # HTTPS
ufw enable
ufw status verbose
```

- postgres (5432) и redis (6379) **НЕ** открывать — они слушают только loopback (см. postgres-redis.md).
- Если порт приложения (gunicorn/uvicorn на TCP) виден наружу — закрой его: трафик только через nginx.
- Проверка: с другой машины `nc -zv VPS_IP 5432` должен отбиваться (connection refused/timeout).

## SSH-hardening

В `/etc/ssh/sshd_config` (или drop-in в `sshd_config.d/`):

```conf
PasswordAuthentication no        # только ключи
PermitRootLogin no               # root по SSH запрещён, заходи под пользователем + sudo
PubkeyAuthentication yes
```

- Перед выключением паролей убедись, что твой публичный ключ в `~/.ssh/authorized_keys`
  (иначе запрёшь себя). Перезапуск: `systemctl restart ssh`.
- Смена порта SSH снижает шум ботов в логах, но это не защита сама по себе (не замена ключам).

## fail2ban (опционально, MEDIUM)

Банит IP после серии неудачных входов (SSH, при желании — nginx):

```bash
apt install fail2ban
# /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 5
bantime = 1h
```

С ключевой аутентификацией SSH fail2ban менее критичен, но снижает мусор в логах и нагрузку
от брутфорса. Для входов в приложение лучше rate-limit на уровне nginx/приложения.

## Права на файлы и каталоги

- Код приложения: владелец `appuser`, без world-writable (`chmod -R o-w`).
- `.env`, `~/.pgpass`, приватные ключи TLS/SSH — `600`.
- `STATIC_ROOT`/`media` — `appuser` пишет, nginx читает (общая группа или права `755`/`644`).
- Никаких `chmod 777` «чтобы заработало» — почти всегда симптом неправильного владельца.

## Обновления и поддержка

- `unattended-upgrades` для security-патчей ОС (или регулярный ручной `apt upgrade`).
- Держи Python-зависимости обновлёнными по безопасности (`pip-audit` локально перед деплоем,
  см. `python-project-audit`).
- LTS-дистрибутив; следи, чтобы версия Python/postgres/redis не вышла из поддержки.

## Частые ошибки (аудит)

- Приложение/nginx под root — CRITICAL.
- Секреты в репозитории или в `Environment=`-строке unit — CRITICAL.
- Нет firewall, БД/redis доступны из интернета — CRITICAL.
- SSH с паролями и/или `PermitRootLogin yes` — HIGH.
- `chmod 777` на коде/конфигах, `.env` читаем всеми — HIGH.
- Нет авто-обновлений безопасности ОС — MEDIUM.
- Один пользователь под все сервисы (бот + веб + cron) — MEDIUM (слабее изоляция при взломе).
