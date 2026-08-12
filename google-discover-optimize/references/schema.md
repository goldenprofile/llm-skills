# JSON-LD для Google Discover

Вставлять в `<head>`. Проверка: Google Rich Results Test.

## NewsArticle (главная разметка статьи)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Заголовок статьи (до 110 символов)",
  "image": [
    "https://example.com/photos/1x1/photo.jpg",
    "https://example.com/photos/4x3/photo.jpg",
    "https://example.com/photos/16x9/photo.jpg"
  ],
  "datePublished": "<ISO 8601 с таймзоной — из модели>",
  "dateModified": "<ISO 8601 с таймзоной — из модели>",
  "author": {
    "@type": "Person",
    "name": "Имя Автора",
    "url": "https://example.com/author/name",
    "jobTitle": "Должность"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Название издания",
    "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}
  },
  "description": "Краткое описание для сниппета (до 160 символов)",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://example.com/article-url"}
}
</script>
```
Даты — реальные значения из модели, формат ISO 8601 с таймзоной. Не хардкодь фиксированные.

## Organization (на главной)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Название издания",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": ["https://t.me/channel", "https://vk.com/group"],
  "contactPoint": {"@type": "ContactPoint", "email": "info@example.com", "contactType": "editorial"}
}
</script>
```

## BreadcrumbList
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Главная", "item": "https://example.com"},
    {"@type": "ListItem", "position": 2, "name": "Статьи", "item": "https://example.com/articles"},
    {"@type": "ListItem", "position": 3, "name": "Заголовок статьи"}
  ]
}
</script>
```
