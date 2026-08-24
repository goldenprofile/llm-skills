# Эталонные JSON-LD шаблоны

Правила: JSON-LD в `<script type="application/ld+json">` в `<head>`; несколько схем —
отдельные блоки или массив `[{...}, {...}]`; `@context: "https://schema.org"`; все
обязательные свойства по spec; валидация — Google Rich Results Test и Schema.org Validator.

> JSON-LD должен приходить в первичном (server-rendered) HTML: JS-вставленную разметку Google
> обрабатывает с задержкой или теряет (руководство по JS SEO, декабрь 2025). Django SSR это
> покрывает штатно — но не вставляй схемы через HTMX/Alpine после загрузки страницы.

Обязательные схемы по типу страницы:

| Тип | Схемы |
|-----|-------|
| Home | Organization, WebSite (SearchAction) |
| Category | BreadcrumbList, ItemList |
| Product | Product (Offer, AggregateRating), BreadcrumbList |
| Article | Article/NewsArticle/BlogPosting, BreadcrumbList, Person/Organization |
| Any | WebPage (рекомендуется) |

## Organization (Home)
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Brand Name",
  "url": "https://example.com/",
  "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png", "width": 200, "height": 60},
  "contactPoint": {"@type": "ContactPoint", "telephone": "+7-000-000-0000", "contactType": "customer service"},
  "sameAs": ["https://vk.com/brand", "https://t.me/brand"]
}
```

## WebSite + SearchAction (Home)
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Brand Name",
  "url": "https://example.com/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {"@type": "EntryPoint", "urlTemplate": "https://example.com/search/?q={search_term_string}"},
    "query-input": "required name=search_term_string"
  }
}
```
`SearchAction` оставлять можно, но SERP-выгоды нет: rich result «sitelinks search box»
Google убрал ещё в 2024 — разметка теперь чисто машиночитаемая. Не продавай её как фичу.

## BreadcrumbList
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/"},
    {"@type": "ListItem", "position": 2, "name": "Category", "item": "https://example.com/cat/"},
    {"@type": "ListItem", "position": 3, "name": "Page Title"}
  ]
}
```
Последний элемент (текущая страница) может быть без `"item"`.

## Product
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "image": ["https://example.com/img/product.jpg"],
  "description": "Product description.",
  "sku": "SKU-001",
  "brand": {"@type": "Brand", "name": "Brand"},
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/product/",
    "priceCurrency": "RUB",
    "price": "1299.00",
    "priceValidUntil": "<дата на год вперёд от текущей>",
    "itemCondition": "https://schema.org/NewCondition",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.5", "reviewCount": "12"}
}
```
`priceValidUntil` — рассчитывай динамически (например, +1 год), не хардкодь фиксированную дату.

## Article / NewsArticle / BlogPosting
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title (max 110 chars)",
  "image": ["https://example.com/img/article.jpg"],
  "author": {"@type": "Person", "name": "Author Name"},
  "publisher": {
    "@type": "Organization",
    "name": "Brand Name",
    "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}
  },
  "datePublished": "<ISO 8601 с таймзоной>",
  "dateModified": "<ISO 8601 с таймзоной>",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://example.com/article/"}
}
```
Даты — реальные значения из модели (`published_at`/`updated_at`), формат ISO 8601 с таймзоной.

### Discover-дельта (только для статей)

Для попадания в Google Discover тот же `NewsArticle` дополняется:

```json
"image": [
  "https://example.com/photos/1x1/photo.jpg",
  "https://example.com/photos/4x3/photo.jpg",
  "https://example.com/photos/16x9/photo.jpg"
],
"author": {
  "@type": "Person",
  "name": "Имя Автора",
  "url": "https://example.com/author/name",
  "jobTitle": "Должность"
},
"description": "Краткое описание для сниппета (до 160 символов)"
```

Три соотношения сторон дают Google выбор превью под формат ленты; `author.url`
и `jobTitle` работают на E-E-A-T. Остальное — см. [discover.md](discover.md).

## FAQPage

> **Статус (07.05.2026):** Google полностью вывел FAQ rich results для всех сайтов — это финал
> ограничения августа 2023 (когда фичу оставили только gov/health). SERP-выгоды больше нет.
> Существующую разметку **не требуй удалять** (она валидна и безвредна — флагуй как Low/Info),
> новую ради Google **не рекомендуй**. Для страниц настоящих вопросов-ответов, где отвечают
> пользователи, используй `QAPage` (поддерживается).

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type": "Question", "name": "Question text?", "acceptedAnswer": {"@type": "Answer", "text": "Answer text."}}
  ]
}
```

## ItemList (Category/Listing)
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Category Name",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "url": "https://example.com/item-1/"},
    {"@type": "ListItem", "position": 2, "url": "https://example.com/item-2/"}
  ]
}
```

## Устаревшие типы — не рекомендуй

| Тип | Статус |
|-----|--------|
| HowTo | rich results убраны в сентябре 2023 |
| SpecialAnnouncement | deprecated с июля 2025 (COVID-схема) |
| CourseInfo, EstimatedSalary, LearningVideo, ClaimReview, VehicleListing | выведены из rich results в июне 2025; с 2026 не проверяются в Rich Results Test / Search Console |
| Practice Problem | deprecated, поддержка в инструментах убрана в январе 2026 |

Если находишь такой тип в аудите — флагуй как Low с датой вывода и заменой (LearningVideo →
VideoObject, FAQPage → QAPage для настоящих Q&A). `Dataset` — **не** выведен: его читает
Google Dataset Search, просто нет rich results в основном поиске; удалять не советуй.
