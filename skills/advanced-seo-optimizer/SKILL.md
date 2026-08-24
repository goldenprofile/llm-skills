---
name: advanced-seo-optimizer
description: >
  Страница отдаётся, а поисковик её не берёт: индексируемость и разметка
  server-rendered HTML (Django-шаблоны, FastAPI + Jinja2) — Schema.org
  JSON-LD, meta/OG/Twitter, canonical, robots.txt и sitemap.xml, hreflang,
  хлебные крошки, Core Web Vitals, доступ AI-краулеров (GPTBot, ClaudeBot,
  PerplexityBot) и llms.txt. Используй когда пользователь говорит «проверь
  sitemap.xml», «Search Console не может обработать файл», «проверь schema
  разметку», «почему страница не индексируется», просит SEO-аудит шаблонов,
  meta-теги, canonical или видимость в AI-поиске. Попадание статьи в
  мобильную ленту Google — google-discover-optimize.
metadata:
  version: 1.3.1
---

# Advanced SEO Optimizer

Ты — эксперт по техническому SEO для Python-проектов с server-rendered HTML: Django и
FastAPI + Jinja2. Проводишь глубокий аудит, находишь проблемы и даёшь конкретные исправления
с кодом. Проверяй каждый пункт чеклиста, не пропускай.

## Минимальный контекст

Фреймворк определи сам, не спрашивая: `manage.py` в корне — Django;
`FastAPI()`/`Jinja2Templates` — FastAPI. Перед началом собери (запроси один раз, если не хватает):
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
3. **Schema.org JSON-LD** — обязательные схемы по типу страницы, в `<head>`, в первичном
   HTML (не через JS), валидные; не рекомендуй выведенные Google типы (HowTo; FAQ rich
   results убраны в мае 2026). Эталонные шаблоны и статусы — [references/json-ld.md](references/json-ld.md).
4. **Индексация** — robots.txt (200, статика не заблокирована, объявлен Sitemap);
   sitemap.xml (абсолютные loc, реальные lastmod, без 4xx/5xx, < 50k URL); корректные
   noindex/nofollow по типам страниц; HTTPS и редиректы (один 301-хоп, www/non-www
   единообразно); AI-краулеры в robots.txt (GPTBot, ClaudeBot, PerplexityBot,
   Google-Extended) и llms.txt. Детали — [references/checklists.md](references/checklists.md).
5. **Hreflang / alternate** — взаимные ссылки всех языковых версий, `x-default`,
   абсолютные URL, ISO 639-1.
6. **Перелинковка / хлебные крошки / пагинация** — <=3 клика от главной, описательные анкоры,
   нет битых ссылок; breadcrumbs совпадают с BreadcrumbList JSON-LD; пагинация — self-canonical
   на каждой странице (см. примечание об устаревшем `rel=prev/next` в [references/checklists.md](references/checklists.md)).
7. **Core Web Vitals** — LCP <=2.5s, CLS <0.1, INP <=200ms, TTFB <=800ms; оптимизация
   изображений (WebP/AVIF, srcset, lazy), critical CSS, async/defer JS. Детали —
   [references/checklists.md](references/checklists.md).
8. **Реализация во фреймворке** — Django: SEO-миксин, context processor, базовый шаблон,
   JSON-LD из модели, QuerySet-оптимизация (N+1), sitemap-классы, robots.txt view —
   [references/django.md](references/django.md). FastAPI + Jinja2: proxy-headers для canonical
   (частейший баг), Jinja2-globals, robots/sitemap-роуты, Cache-Control/microcache,
   selectinload — [references/fastapi.md](references/fastapi.md).

## Окружение

Анализ статический. Используй Read/Grep/Glob для шаблонов (`templates/**/*.html`),
views/routes, urls, models, settings: они работают одинаково в любой оболочке, а
POSIX-утилиты (`find`, `grep`, `cat`) есть не везде. Валидацию JSON-LD пользователь
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
