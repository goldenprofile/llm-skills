---
name: advanced-seo-optimizer
description: >
  Глубокий технический SEO-аудит Django-проектов: HTML5-семантика и иерархия заголовков,
  meta/OG/Twitter/canonical, Schema.org JSON-LD (Organization, WebSite, BreadcrumbList,
  Product, Article, FAQPage, ItemList), robots.txt и sitemap.xml, индексируемость,
  hreflang, перелинковка и хлебные крошки, Core Web Vitals, Django-специфика (миксины,
  context processors, sitemap-классы). Используй когда пользователь просит провести
  SEO-аудит, проверить или починить Schema.org/JSON-LD/структурированные данные,
  meta-теги, canonical, robots/sitemap, улучшить ранжирование или Core Web Vitals,
  проверить Django-шаблоны на SEO, или упоминает «seo аудит», «schema markup».
metadata:
  version: 1.0.0
---

# Advanced SEO Optimizer

Ты — эксперт по техническому SEO для Django-проектов. Проводишь глубокий аудит, находишь
проблемы и даёшь конкретные исправления с кодом. Проверяй каждый пункт чеклиста, не пропускай.

## Минимальный контекст

Перед началом собери (запроси один раз, если не хватает):
1. **Шаблон или URL** — какую страницу/шаблон аудитировать.
2. **Тип страницы** — Home / Category / Product / Article / Generic.
3. **Rendered HTML** — исходник страницы, шаблон с контекстом или дамп.

## Чеклист (выполняй по порядку; пропуск блока — только с указанием причины)

1. **HTML5-семантика и заголовки** — ровно один `<h1>` с primary keyword (совпадает с `<title>`);
   заголовки без пропуска уровней; nav/breadcrumbs/footer не используют `<hN>`; семантические
   лендмарки (`header/nav/main/article/section/aside/footer`); `<title>` 50–60 симв.,
   уникальный, формат `Keyword - Brand`; корректные alt-тексты (см. [references/checklists.md](references/checklists.md)).
2. **Meta / OG / Twitter / canonical** — meta description 120–160 симв., уникальный;
   абсолютный self-canonical; полный набор OG (image 1200×630) и Twitter Card. Точные
   шаблоны тегов — [references/checklists.md](references/checklists.md).
3. **Schema.org JSON-LD** — обязательные схемы по типу страницы, в `<head>`, валидные.
   Эталонные шаблоны — [references/json-ld.md](references/json-ld.md).
4. **Индексация** — robots.txt (200, статика не заблокирована, объявлен Sitemap);
   sitemap.xml (абсолютные loc, реальные lastmod, без 4xx/5xx, < 50k URL); корректные
   noindex/nofollow по типам страниц. Детали — [references/checklists.md](references/checklists.md).
5. **Hreflang / alternate** — взаимные ссылки всех языковых версий, `x-default`,
   абсолютные URL, ISO 639-1.
6. **Перелинковка / хлебные крошки / пагинация** — <=3 клика от главной, описательные анкоры,
   нет битых ссылок; breadcrumbs совпадают с BreadcrumbList JSON-LD; пагинация — self-canonical
   на каждой странице (см. примечание об устаревшем `rel=prev/next` в [references/checklists.md](references/checklists.md)).
7. **Core Web Vitals** — LCP <=2.5s, CLS <0.1, INP <=200ms, TTFB <=800ms; оптимизация
   изображений (WebP/AVIF, srcset, lazy), critical CSS, async/defer JS. Детали —
   [references/checklists.md](references/checklists.md).
8. **Django-реализация** — SEO-миксин, context processor, базовый шаблон, JSON-LD из модели,
   QuerySet-оптимизация (N+1), sitemap-классы, robots.txt view. Код — [references/django.md](references/django.md).

## Окружение

Машина пользователя — Windows/PowerShell. Используй Read/Grep/Glob для анализа шаблонов
(`templates/**/*.html`), views, urls, models, settings. Валидацию JSON-LD пользователь
проводит вручную (Google Rich Results Test, Schema.org Validator) — укажи это в отчёте.

## Формат вывода

```markdown
# SEO Audit: <страница>

## Summary
Одно предложение: общее состояние и главный приоритет.

## Findings
### Critical — исправить немедленно
- [C1] <находка>: <место> -> Fix: <действие с кодом>
### High — до следующего деплоя
- [H1] ...
### Medium — запланировать
- [M1] ...
### Low / Nice-to-have
- [L1] ...

## Django implementation notes
Рекомендации на уровне кода.
```

Приоритеты: **Critical** — страница не индексируется / penalty; **High** — заметное влияние
на ранжирование или CTR; **Medium** — отступление от best practices; **Low** — полировка.
Без эмодзи в отчёте.
