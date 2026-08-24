# FastAPI (Jinja2) — реализация SEO

Чеклисты и JSON-LD-шаблоны навыка фреймворк-независимы; здесь — эквиваленты Django-механик
для FastAPI + Jinja2. Блочная структура base.html из [django.md](django.md) переносится в
Jinja2 почти без изменений — синтаксис `{% block %}` совпадает с DTL.

## Абсолютные URL за прокси — проверяй первым

За nginx uvicorn видит `http://` и внутренний host: `request.url` / `request.url_for()`
сгенерируют `http://…` в canonical, OG и sitemap — для Google это другой URL. Частейший
SEO-баг FastAPI-деплоя.

```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```
uvicorn: `--proxy-headers --forwarded-allow-ips="127.0.0.1"` (или `ProxyHeadersMiddleware`).

Аудит: ищи в rendered HTML canonical/OG/`<loc>` с `http://` или внутренним хостом — Critical.

## SEO-константы и canonical (аналог context processor)

```python
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    SITE_NAME="Brand Name",
    CANONICAL_DOMAIN="https://example.com",
    DEFAULT_OG_IMAGE="https://example.com/static/img/og-default.jpg",
)

def canonical_url(request: Request) -> str:
    return str(request.url.replace(query=""))  # canonical без query-параметров

templates.env.globals["canonical_url"] = canonical_url
```

В base.html (дополни существующие блоки title/description):
```html
<link rel="canonical" href="{% block canonical %}{{ canonical_url(request) }}{% endblock %}">
<meta property="og:url" content="{{ canonical_url(request) }}">
{% block schema_org %}{% endblock %}
```

## JSON-LD из route (аналог get_context_data)

```python
@app.get("/items/{slug}", response_class=HTMLResponse)
async def item_detail(request: Request, slug: str, repo: ItemRepo = Depends(get_repo)):
    item = await repo.get_by_slug(slug)
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": item.name,
        "offers": {"@type": "Offer", "price": str(item.price), "priceCurrency": "RUB",
                   "availability": "https://schema.org/InStock"},
    }
    return templates.TemplateResponse(request, "item.html", {
        "item": item,
        "schema_json": json.dumps(schema, ensure_ascii=False),
    })
```
Шаблон: `<script type="application/ld+json">{{ schema_json | safe }}</script>` — в `<head>`,
в первичном HTML (не HTMX/JS-вставкой после загрузки).

## robots.txt

```python
@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {CANONICAL_DOMAIN}/sitemap.xml\n"
```

## sitemap.xml (аналога contrib.sitemaps нет — роут руками)

```python
@app.get("/sitemap.xml")
async def sitemap(session: AsyncSession = Depends(get_session)) -> Response:
    urls: list[tuple[str, datetime | None]] = [(f"{CANONICAL_DOMAIN}/", None)]
    rows = await session.execute(
        select(Item.slug, Item.updated_at).where(Item.is_published)
    )
    urls += [(f"{CANONICAL_DOMAIN}/items/{slug}", upd) for slug, upd in rows]
    items = "".join(
        f"<url><loc>{loc}</loc>"
        + (f"<lastmod>{lm:%Y-%m-%d}</lastmod>" if lm else "")
        + "</url>"
        for loc, lm in urls
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>')
    return Response(xml, media_type="application/xml")
```
`lastmod` — реальный `updated_at` из БД, не текущая дата. При большом числе URL кэшируй
результат (Redis/TTL) — иначе каждый обход краулера дёргает полную выборку.

## Trailing slash

FastAPI по умолчанию 307-редиректит `/path/` <-> `/path` (`redirect_slashes=True`). Выбери
один канонический вариант, объявляй все роуты единообразно (обычно без слэша); redirect —
подстраховка, canonical всегда указывает канонический вариант.

## TTFB и кэширование (аналога cache_page нет)

- `Cache-Control: public, max-age=…` на публичных страницах — middleware или прямо в route.
- nginx microcache (`proxy_cache`, 1–10 с) — самый дешёвый способ снять TTFB на анонимном
  трафике, без изменений в коде.
- fastapi-cache2 + Redis — для тяжёлых выборок/фрагментов.
- Статика в проде — через nginx (`expires`, `immutable`), не через `StaticFiles`.

## N+1 (SQLAlchemy 2.x async)

- `selectinload()` для коллекций, `joinedload()` для *-to-one — в запросе, до рендера
  шаблона: lazy load в async-контексте упадёт с `MissingGreenlet`, а не молча затормозит.
- Индексы на `slug` / `is_published` / `updated_at`; LIMIT на list-страницах.

## Чек аудита FastAPI-проекта

- [ ] В base.html есть блоки canonical / OG / schema_org (не только title/description)
- [ ] proxy-headers настроены: в rendered HTML нет `http://` и внутренних хостов
- [ ] `/robots.txt` и `/sitemap.xml` отвечают 200; sitemap объявлен в robots.txt
- [ ] `lastmod` в sitemap — из БД, все `<loc>` абсолютные с канонического домена
- [ ] JSON-LD рендерится в первичном HTML, не подгружается HTMX/JS
- [ ] Cache-Control / microcache на анонимных страницах; статика через nginx
