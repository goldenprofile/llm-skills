# nginx как reverse-proxy для Python-приложений

nginx нужен только HTTP-приложениям (Django/FastAPI). Polling-бот без HTTP его не использует.
Роль nginx: TLS-терминация, отдача статики/медиа, gzip, таймауты, security-заголовки,
проксирование на gunicorn/uvicorn (socket предпочтительнее порта).

## server-блок: TLS + проксирование на socket + статика

`/etc/nginx/sites-available/myapp.conf` (симлинк в `sites-enabled/`):

```nginx
# upstream на unix-socket из systemd-юнита (RuntimeDirectory=myapp)
upstream myapp {
    server unix:/run/myapp/gunicorn.sock fail_timeout=0;
}

# 1) HTTP → HTTPS редирект (кроме ACME-челленджа certbot)
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;

    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

# 2) HTTPS
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    # современный конфиг ssl_ciphers/ssl_dhparam подтянет certbot через include options-ssl-nginx.conf

    server_tokens off;                       # не светить версию nginx
    client_max_body_size 25m;                # размер загрузки (под аплоады; default 1m мал)

    # security-заголовки
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # gzip
    gzip on;
    gzip_vary on;
    gzip_comp_level 5;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml image/svg+xml;

    # СТАТИКА — отдаёт nginx, не приложение (collectstatic в STATIC_ROOT)
    location /static/ {
        alias /opt/myapp/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }

    # МЕДИА (пользовательские загрузки)
    location /media/ {
        alias /opt/myapp/media/;
        expires 7d;
    }

    # ПРИЛОЖЕНИЕ
    location / {
        proxy_pass http://myapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;     # Django: SECURE_PROXY_SSL_HEADER
        proxy_redirect off;

        # таймауты (по умолчанию 60s; ставь под реальные долгие запросы)
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
    }
}
```

## TLS через certbot

```bash
# nginx-плагин сам впишет ssl-директивы и настроит редирект:
certbot --nginx -d example.com -d www.example.com
# проверка авто-продления (таймер certbot.timer ставится автоматически):
certbot renew --dry-run
```

- Авто-renew работает через systemd-таймер `certbot.timer` (или cron в старых системах) — проверь
  `systemctl list-timers | grep certbot`. Без продления сертификат протухнет через 90 дней (HIGH).
- Для webhook-приёмника бота (если перейдёт на webhook) — тот же TLS-блок, `proxy_pass` на порт/socket aiohttp.

## Django-специфика за nginx

- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — иначе Django считает запрос HTTP.
- `ALLOWED_HOSTS` = домены; `CSRF_TRUSTED_ORIGINS = ["https://example.com"]`.
- `python manage.py collectstatic` в `STATIC_ROOT` (= `alias` в `location /static/`).
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE = True` в проде.
- `DEBUG = False` (иначе утечка трейсбеков + Django сам не должен отдавать статику в проде).

## Частые ошибки (аудит)

- **Нет TLS / HTTP наружу** (CRITICAL): пароли/куки в открытом виде. Нужен certbot + редирект 80→443.
- **Статику отдаёт приложение** (gunicorn/WhiteNoise на больших объёмах) — медленно; nginx через `alias`.
- `client_max_body_size` по умолчанию (1m) → загрузки крупнее падают с 413.
- Таймауты по умолчанию (60s) при долгих запросах рвут соединение — либо поднять, либо вынести в фон.
- Нет `server_tokens off` и security-заголовков (MEDIUM).
- `proxy_pass` на `127.0.0.1:port`, открытый наружу через firewall — приложение доступно мимо nginx.
- gzip выключен — лишний трафик и латентность на JSON/HTML (MEDIUM).
- `add_header` без `always` не ставится на ответы с ошибками (4xx/5xx).
