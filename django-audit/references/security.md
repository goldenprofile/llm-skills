# Линза: security

Security-аудит по OWASP Top 10 + Django-специфика. Префикс находок: `SEC`.
Указывай тип (`A0X:2021`) и, где уместно, оценку CVSS. Лучше false positive, чем
пропущенная уязвимость.

## OWASP Top 10 (Django)

### A01 Broken Access Control
```python
# IDOR — объект по id из URL без проверки владельца:
user = User.objects.get(id=user_id)        # нет request.user == user
Document.objects.get(pk=request.GET['id'])
def admin_panel(request): ...              # нет @login_required/@staff_member_required
```
- [ ] У всех protected-views проверка авторизации (`@login_required`/`LoginRequiredMixin`)
- [ ] IDOR-защита: проверка владельца; `get_queryset()` фильтрует по `request.user`

### A02 Cryptographic Failures
```python
hashlib.md5(password); hashlib.sha1(password)   # слабое хеширование
SECRET_KEY = 'hardcoded'; API_KEY = 'sk_live_x' # хардкод секретов
SECURE_SSL_REDIRECT = False; SESSION_COOKIE_SECURE = False; CSRF_COOKIE_SECURE = False
```
- [ ] SECRET_KEY из env; нет хардкода паролей/ключей/токенов; HTTPS enforced в prod

### A03 Injection
```python
cursor.execute(f"... WHERE name = '{name}'")    # SQL
Model.objects.raw(f"SELECT * FROM {table}")
Model.objects.extra(where=[f"name = '{name}'"])
os.system(f"convert {filename}")                 # command
subprocess.call(f"ls {path}", shell=True)
eval(user_input); exec(user_input)
Template(user_input).render()                    # template injection
```
- [ ] Весь SQL через ORM/параметризованные запросы; нет `shell=True` с вводом; нет `eval/exec` с внешними данными

### A04 Insecure Design
```python
token = str(user.id)                             # предсказуемый токен
token = hashlib.md5(email).hexdigest()
# PasswordResetToken без времени жизни
```

### A05 Security Misconfiguration (settings.py)
```python
DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True
DATABASES = {'default': {'PASSWORD': ''}}        # пустой пароль
```
- [ ] `DEBUG = False`; `ALLOWED_HOSTS` только нужные домены; `SECRET_KEY` из env
- [ ] `SECURE_HSTS_SECONDS` > 0; `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
      `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF` = True; `X_FRAME_OPTIONS = 'DENY'`

### A07 Authentication Failures
```python
AUTH_PASSWORD_VALIDATORS = []                            # пустой
logger.info(f"... password {password}")                  # пароль в логах
if user.password == submitted_password: ...              # timing attack
```

### A08 Data Integrity Failures
```python
pickle.loads(user_data)
yaml.load(user_input)                            # без Loader=SafeLoader
```

### A09 Logging Failures
```python
logger.info(f"Password: {password}")
logger.debug(f"Credit card: {card_number}")
logger.info(f"Token: {api_token}")
```

### A10 SSRF
```python
requests.get(user_provided_url)
urllib.request.urlopen(url_from_input)
```

## Django-специфика
```python
@csrf_exempt                                     # почему отключено?
<form method="POST">                             # без {% csrf_token %}
{{ variable|safe }}; {% autoescape off %}; mark_safe(user_input)   # XSS
User.objects.create(**request.POST)              # mass assignment
class Meta: fields = '__all__'                   # включая is_superuser
open(f"/uploads/{filename}")                     # path traversal
# unrestricted upload: request.FILES без проверки типа/размера/имени
```

## Секреты (Grep)
```
password\s*=\s*['"][^'"]+['"]
api_key\s*=\s*['"][^'"]+['"]
secret\s*=\s*['"][^'"]+['"]
token\s*=\s*['"][^'"]+['"]
AWS_ACCESS_KEY | AWS_SECRET | STRIPE_ | sk_live_ | sk_test_
-----BEGIN RSA PRIVATE KEY-----
```

Примечание: ссылайся на актуальную редакцию OWASP Top 10 на момент аудита
(категории выше — редакция 2021; проверь, не вышла ли новее).
