# Детальные чеклисты SEO-аудита

## 1. HTML5-семантика и заголовки
- Ровно один `<h1>` с primary keyword, совпадает с `<title>`.
- Заголовки по порядку H1→H2→H3 без пропуска уровней.
- nav/breadcrumbs/footer не используют `<hN>`.
- Лендмарки: `<header>`, `<nav aria-label="...">`, `<main>` (один), `<article>`, `<section>`, `<aside>`, `<footer>`; нет `<div class="header">` вместо тегов.
- `<title>` 50–60 символов, формат `Primary Keyword - Brand`, уникален.

Alt-тексты:
| Случай | alt |
|--------|-----|
| Информативное | Краткое описание + ключевое слово |
| Декоративное | `alt=""` (пустой, не отсутствующий) |
| Ссылочное | Описание цели ссылки |
| Текст на картинке | Воспроизвести текст |

Для статей (E-E-A-T): видимый байлайн автора и даты публикации/обновления на странице,
совпадающие с `author`/`datePublished`/`dateModified` в Article JSON-LD.

## 2. Meta / OG / Twitter / canonical
- Meta description 120–160 символов, уникальный, с CTA; авто-фоллбэк из модели/первых ~155 символов.
- Canonical: всегда абсолютный URL, self-canonical на каждой странице; HTTP `Link: rel="canonical"` как фоллбэк.

Open Graph:
```html
<meta property="og:title" content="...">
<meta property="og:description" content="120-300 chars">
<meta property="og:image" content="https://example.com/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://example.com/page/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Brand Name">
<meta property="og:locale" content="ru_RU">
```
OG image: >=1200×630, < 1 MB, JPEG предпочтительно.

Twitter Card:
```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@handle">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="max 200 chars">
<meta name="twitter:image" content="https://example.com/img/twitter.jpg">
<meta name="twitter:image:alt" content="...">
```

## 4. Индексация
robots.txt: существует (200, не 404/редирект); блок `User-agent: *`; нет случайного `Disallow: /`;
статика не заблокирована; объявлен `Sitemap:`; staging имеет `Disallow: /`.

sitemap.xml: по `/sitemap.xml` или объявлен в robots; `Content-Type: application/xml`;
все публичные индексируемые URL; нет 4xx/5xx и заблокированных в robots; реальный `<lastmod>`;
абсолютные `<loc>`; < 50 MB и < 50 000 URL (иначе разбить на индекс).

noindex/nofollow:
| Случай | Тег |
|--------|-----|
| Thin/дубликат | `noindex,follow` |
| Закрытая страница | `noindex,nofollow` + серверная авторизация |
| Страница поиска | `noindex,follow` |
| Страница "Спасибо" | `noindex,nofollow` |

HTTPS и редиректы: HTTPS принудительно, валидный сертификат, нет mixed content;
редирект в один 301-хоп (без цепочек); www/non-www и слэш на конце — единообразно
(`APPEND_SLASH`, `PREPEND_WWW` / настройка nginx).

Лимит Googlebot: индексируются первые **~2 МБ HTML** — критичный контент и JSON-LD размещай
в начале документа; не раздувай `<head>` inline-CSS/JS и base64-картинками.

JS и индексация (руководство Google по JS SEO, декабрь 2025): canonical, meta robots и
JSON-LD должны быть в **первичном HTML-ответе** — при конфликте raw HTML и JS-вставки Google
может взять любую версию, а страницы с не-200 статусом вообще не рендерятся. Django SSR это
покрывает штатно; осторожно с мета-тегами, вставляемыми через HTMX/Alpine/JS.

AI-краулеры в robots.txt:
| Краулер | Владелец | Назначение |
|---------|----------|------------|
| GPTBot | OpenAI | обучение моделей |
| OAI-SearchBot | OpenAI | поиск ChatGPT |
| ChatGPT-User | OpenAI | user-triggered browsing — robots.txt не действует |
| ClaudeBot | Anthropic | обучение / веб-фичи Claude |
| PerplexityBot | Perplexity | индекс Perplexity |
| Google-Extended | Google | обучение Gemini — НЕ влияет на Google Search / AI Overviews |
| CCBot | Common Crawl | открытый датасет (часто блокируют) |
| Bytespider | ByteDance | обучение |

- Блокировка `Google-Extended` не убирает сайт из поиска и AI Overviews — их обслуживает Googlebot.
- User-triggered фетчеры (ChatGPT-User, Google-Agent, Google-NotebookLM) игнорируют robots.txt
  by design — ограничивать только на уровне сервера.
- Для видимости в AI-поиске (ChatGPT, Perplexity, Claude) поисковые AI-боты обычно стоит
  разрешать; блокируй осознанно и адресно, а не `User-agent: *` скопом.
- Появлением в AI Overviews / AI Mode управляют стандартные директивы (`noindex`, `nosnippet`,
  `data-nosnippet`, `max-snippet`) — отдельного «AI-опт-аута» у Google нет.
- llms.txt: Google Search его **официально игнорирует** («не поможет и не навредит» — AI
  optimization guide, июнь 2026). Не преподноси как фактор ранжирования; опционален для
  прочих AI-сервисов — если есть, пусть лежит, если нет — не Critical/High.

## 6. Перелинковка / хлебные крошки / пагинация
- Каждая индексируемая страница <=3 клика от главной; описательные анкоры (не «нажмите здесь»).
- Нет битых ссылок; используется `<a href>` (не JS-only); важные внутренние страницы без `rel="nofollow"`.
- Breadcrumbs на всех страницах кроме Home; совпадают с BreadcrumbList JSON-LD; в `<nav aria-label="Breadcrumb">`; Home первый, текущая последняя без ссылки.
- Пагинация: **self-canonical на каждой странице** (НЕ canonical на page=1).

> Устаревшее: `<link rel="prev"/"next">` для пагинации Google официально **не использует с 2019 года**.
> Не рекомендуй их как фактор SEO. Для UX/доступности они допустимы, но это не влияет на индексирование.
> Для больших списков рассмотри подгрузку/«показать все» или внятную пагинацию с уникальными title/description.

## 7. Core Web Vitals
- **LCP <= 2.5s**: hero `fetchpriority="high"` + `<link rel="preload" as="image">`; серверный кэш; нет render-blocking ресурсов выше fold.
- **CLS < 0.1**: явные `width`/`height` у `<img>`/`<video>`; резерв места под рекламу/эмбеды/lazy; `font-display: swap`.
- **INP <= 200ms**: нет long tasks (>50ms) в обработчиках; defer некритичного JS; `requestIdleCallback` для аналитики; DOM < 1500 узлов. (INP заменил FID в наборе Core Web Vitals с марта 2024 — FID больше не используется.)
- **TTFB <= 800ms**: `cache_page` на тяжёлых views; `select_related`/`prefetch_related`; Redis-кэш; CDN/WhiteNoise для статики.
- Изображения: WebP/AVIF с фоллбэком через `<picture>`; `srcset`/`sizes`; `loading="lazy"` ниже fold; < 150 KB для контентных.
- CSS/JS: critical CSS инлайн (< 14 KB); некритичный CSS через `preload`+`onload`; сторонние скрипты `async`/`defer`.
