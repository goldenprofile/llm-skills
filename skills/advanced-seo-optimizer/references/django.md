# Django-реализация SEO

## SEO-миксин для моделей
```python
class SEOMixin(models.Model):
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=165, blank=True)
    canonical_url = models.URLField(blank=True)

    class Meta:
        abstract = True

    def get_seo_title(self):
        return self.seo_title or str(self)

    def get_seo_description(self):
        return self.seo_description or getattr(self, "description", "")[:155]
```
> Не добавляй поле `seo_keywords` / meta keywords: Google игнорирует `<meta name="keywords">`
> с 2009 года, оно бесполезно для ранжирования и лишь захламляет модель.

## Context processor
```python
def seo_defaults(request):
    return {
        "SITE_NAME": "Brand Name",
        "DEFAULT_OG_IMAGE": "/static/img/og-default.jpg",
        "CANONICAL_DOMAIN": "https://example.com",
    }
```

## Базовый шаблон (SEO-блоки)
```html
{# base.html #}
<head>
  <title>{% block seo_title %}{{ SITE_NAME }}{% endblock %}</title>
  <meta name="description" content="{% block seo_description %}{% endblock %}">
  <link rel="canonical" href="{% block canonical %}{{ request.build_absolute_uri }}{% endblock %}">
  {% block og_tags %}
  <meta property="og:title" content="{% block og_title %}{{ SITE_NAME }}{% endblock %}">
  <meta property="og:description" content="{% block og_description %}{% endblock %}">
  <meta property="og:image" content="{% block og_image %}{{ DEFAULT_OG_IMAGE }}{% endblock %}">
  <meta property="og:url" content="{% block og_url %}{{ request.build_absolute_uri }}{% endblock %}">
  <meta property="og:type" content="{% block og_type %}website{% endblock %}">
  {% endblock %}
  {% block schema_org %}{% endblock %}
</head>
```

## JSON-LD из инстанса модели
```python
class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": obj.name,
            "description": obj.description,
            "offers": {
                "@type": "Offer",
                "price": str(obj.price),
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock",
            },
        }
        ctx["schema_json"] = mark_safe(json.dumps(schema, ensure_ascii=False))
        return ctx
```

## QuerySet-оптимизация (против N+1)
- [ ] `select_related` на FK/OneToOne, используемых в шаблонах
- [ ] `prefetch_related` на M2M/reverse FK
- [ ] `only()`/`defer()` на list-страницах
- [ ] Индексы БД на `slug`, `is_published`, `created_at`
- [ ] `cache_page` на публичных list/detail views
- [ ] Django Debug Toolbar в dev для проверки N+1

## Sitemap (django.contrib.sitemaps)
```python
class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at
```

## robots.txt view
```python
urlpatterns += [
    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain",
    )),
]
```
