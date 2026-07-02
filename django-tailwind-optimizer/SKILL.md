---
name: django-tailwind-optimizer
description: Анализирует Django шаблоны на использование Tailwind CSS, выявляет дублирование стилей, оптимизирует для production. Используй когда пользователь работает с Django templates и Tailwind CSS, просит оптимизировать CSS, отрефакторить шаблоны, перейти с Tailwind CDN на production-ready сборку, или говорит «оптимизируй tailwind», «убери дублирование стилей», «подготовь CSS к продакшену».
metadata:
  version: 2.0.0
---

# Django Tailwind Optimizer

Навык для анализа и оптимизации Django шаблонов с Tailwind CSS. Помогает перейти от CDN версии к production-ready конфигурации, выявляет дублирование и оптимизирует финальный CSS.

Основной путь — **Tailwind CSS v4** (CSS-first конфигурация). Для существующих
проектов на v3 — ветка Legacy в [references/migration.md](references/migration.md).

## Когда использовать

- Нужно проанализировать использование Tailwind в Django шаблонах
- Переход с Tailwind CDN на оптимизированную сборку
- Выявление дублированных стилей в `<style>` блоках
- Подготовка CSS к production (purge, minify)
- Рефакторинг шаблонов для лучшей переиспользуемости

## Шаг 0. Определи версию Tailwind в проекте (ОБЯЗАТЕЛЬНО первым)

v3 и v4 несовместимы по конфигурации — не выдавай рекомендации, пока не определил версию:

| Признак | Версия |
|---|---|
| `input.css` начинается с `@import "tailwindcss"`, есть `@theme` | **v4** |
| `@tailwind base; @tailwind components; @tailwind utilities;` | **v3** |
| `tailwind.config.js` с `module.exports = { content: [...] }` — единственный конфиг | **v3** |
| `package.json`: `"tailwindcss": "^4..."` / `"@tailwindcss/cli"` | **v4** |
| `package.json`: `"tailwindcss": "^3..."` | **v3** |
| Только CDN `<script src="https://cdn.tailwindcss.com">` | версии нет — новый сетап делай на **v4** |

- Проект уже на v4 → работай по этому файлу.
- Проект на v3 и миграция не входит в задачу → работай по ветке Legacy v3
  ([references/migration.md](references/migration.md), § Legacy), **не смешивай** синтаксисы.
- Проект на v3 и хочет обновиться → план v3→v4 там же.
- Внимание: если скачать standalone CLI `latest` (это v4) и скормить ему v3-конфиг
  с `@tailwind`-директивами — сборка не заработает. Версия бинаря и синтаксис
  конфигурации обязаны совпадать.

## Быстрый старт

### 1. Анализ текущего состояния

При первом запросе на оптимизацию:

1. Найти все HTML шаблоны (Glob `templates/**/*.html`)
2. Проверить способ подключения Tailwind (Grep по шаблонам):
   - CDN через `<script src="https://cdn.tailwindcss.com">`
   - Standalone CLI
   - NPM (`@tailwindcss/cli` / PostCSS / Vite)
   - django-tailwind пакет
3. Собрать статистику использования:
   - Количество шаблонов
   - Встроенные `<style>` блоки (дублирование)
   - Конфигурация: `@theme` в CSS (v4) или `tailwind.config.js` (v3)
   - Используемые классы Tailwind

### 2. Выявление проблем

**Типичные проблемы с Tailwind CDN:**

- Загружается весь фреймворк (мегабайты) вместо нужных классов
- Дублирование CSS в разных шаблонах
- Нет минификации, нет tree-shaking неиспользуемых классов
- Медленная загрузка на production

### 3. Варианты оптимизации

**Вариант A: Standalone CLI (рекомендуемый для Django без Node.js)**
- Плюс: не требует Node.js ни в dev, ни на production
- Плюс: простая настройка, автоматическое обнаружение классов (v4)
- Минус: требует запуск watch-процесса при разработке

**Вариант B: NPM + `@tailwindcss/cli` или Vite (полный контроль)**
- Плюс: интеграция с другими фронтенд-инструментами
- Минус: требует Node.js окружение

**Вариант C: django-tailwind пакет**
- Плюс: Django-native решение, hot-reload
- Минус: дополнительная зависимость; проверь поддержку v4 перед выбором

## Оптимизация: Standalone CLI v4

### Шаг 1: Установка (Windows / PowerShell)

Фиксируй версию явно (проверь актуальный тег v4-линейки на
https://github.com/tailwindlabs/tailwindcss/releases — на момент написания v4.3.2).
Не используй `latest` в скриптах — мажорный релиз молча сломает сборку:

```powershell
$v = "v4.3.2"
Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/$v/tailwindcss-windows-x64.exe" -OutFile "tailwindcss.exe"
```

На Linux-сервере аналогично: `tailwindcss-linux-x64` того же тега.

### Шаг 2: Создать input.css (конфигурация живёт в CSS, tailwind.config.js не нужен)

```css
/* static/src/tailwind.css */
@import "tailwindcss";

/* Где искать классы. v4 сканирует проект автоматически (уважая .gitignore),
   но для Django явные источники надёжнее: */
@source "../../templates";
@source "../../apps";

/* Тема — CSS-переменные вместо tailwind.config.js */
@theme {
  --color-primary: #4f46e5;
  --color-secondary: #10b981;
}

/* Кастомные компоненты из <style> блоков */
@layer components {
  .domain-card {
    @apply transition-all duration-300 hover:-translate-y-1 hover:shadow-xl;
  }
}
```

### Шаг 3: Сборка (PowerShell)

```powershell
# Development (watch mode)
.\tailwindcss.exe -i .\static\src\tailwind.css -o .\static\dist\tailwind.css --watch

# Production (minified)
.\tailwindcss.exe -i .\static\src\tailwind.css -o .\static\dist\tailwind.min.css --minify
```

### Шаг 4: Обновить base.html

```html
<!-- Заменить CDN на локальный файл -->
{% load static %}
<link rel="stylesheet" href="{% static 'dist/tailwind.min.css' %}">

<!-- Удалить: -->
<!-- <script src="https://cdn.tailwindcss.com"></script> -->
<!-- <script>tailwind.config = {...}</script> -->
```

Пошаговый план миграции CDN → v4 по фазам (подготовка → извлечение стилей →
обновление base → очистка → deploy) — в
[references/migration.md](references/migration.md).

## Рефакторинг дублированных стилей

Паттерны не зависят от версии (v4/v3 — `@layer components` и `@apply` работают в обеих).

### Повторяющиеся утилиты → Компонент

**До:**
```html
<button class="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow transition">Кнопка 1</button>
<button class="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow transition">Кнопка 2</button>
```

**После:**
```css
@layer components {
  .btn-primary {
    @apply bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow transition;
  }
}
```
```html
<button class="btn-primary">Кнопка 1</button>
<button class="btn-primary">Кнопка 2</button>
```

### `<style>` блоки в шаблонах → централизованный input.css

**До (дублирование в каждом файле):**
```html
<!-- templates/dashboard/index.html -->
<style>
  .domain-card { transition: all 0.3s ease; }
  .domain-card:hover { transform: translateY(-5px); }
</style>
```

**После:** правило один раз в `input.css` → `@layer components` (см. Шаг 2),
`<style>` блок из шаблона удаляется.

### Inline стили → Tailwind классы

**До:**
```html
<style>
  .custom-card { background-color: #fff; border-radius: 8px; padding: 24px; }
</style>
```

**После:**
```html
<div class="bg-white rounded-lg p-6 shadow-sm">
```

## Ожидаемый результат

Типичный порядок величин (зависит от проекта и числа использованных классов —
это ориентир, не гарантия):

```
До (CDN):
- tailwindcss CDN: мегабайты, без кеширования сборки
- Первая загрузка: секунды

После (optimized):
- tailwind.min.css: 30-80 KB (сжатый: 5-15 KB)
- Кеширование: 1 год (immutable по хешу или версии)
```

## Чеклист перед production

- [ ] Версия Tailwind определена (Шаг 0), синтаксис конфига соответствует версии
- [ ] Версия standalone CLI зафиксирована (не `latest`)
- [ ] Все `<style>` блоки перенесены в `input.css`
- [ ] CDN скрипты удалены из шаблонов
- [ ] `@source` покрывает все каталоги с шаблонами и python-кодом с классами
- [ ] CSS собран с флагом `--minify`
- [ ] Проверен размер финального CSS (ориентир < 50KB до сжатия)
- [ ] Django `collectstatic` выполнен, nginx кеширует CSS

## Справочники

- [references/migration.md](references/migration.md) — план миграции CDN → v4 по
  фазам; апгрейд v3 → v4; ветка Legacy v3 (проекты, остающиеся на v3, и
  ограничения браузеров v4: Safari 16.4+, Chrome 111+, Firefox 128+).
