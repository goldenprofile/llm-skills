---
name: django-tailwind-optimizer
description: Анализирует Django шаблоны на использование Tailwind CSS, выявляет дублирование стилей, оптимизирует для production. Используй когда пользователь работает с Django templates и Tailwind CSS, просит оптимизировать CSS, отрефакторить шаблоны, перейти с Tailwind CDN на production-ready сборку, или говорит «оптимизируй tailwind», «убери дублирование стилей», «подготовь CSS к продакшену».
metadata:
  version: 1.0.0
---

# Django Tailwind Optimizer

Навык для анализа и оптимизации Django шаблонов с Tailwind CSS. Помогает перейти от CDN версии к production-ready конфигурации, выявляет дублирование и оптимизирует финальный CSS.

## Когда использовать

- Нужно проанализировать использование Tailwind в Django шаблонах
- Переход с Tailwind CDN на оптимизированную сборку
- Выявление дублированных стилей в `<style>` блоках
- Подготовка CSS к production (purge, minify)
- Рефакторинг шаблонов для лучшей переиспользуемости

## Быстрый старт

### 1. Анализ текущего состояния

При первом запросе на оптимизацию:

1. Найти все HTML шаблоны (Glob `templates/**/*.html`)
2. Проверить способ подключения Tailwind (Grep по шаблонам):
   - CDN через `<script src="https://cdn.tailwindcss.com">`
   - Standalone CLI
   - NPM + PostCSS
   - django-tailwind пакет

3. Собрать статистику использования:
   - Количество шаблонов
   - Встроенные `<style>` блоки (дублирование)
   - Кастомные конфигурации `tailwind.config`
   - Используемые классы Tailwind

### 2. Выявление проблем

**Типичные проблемы с Tailwind CDN:**

- Загружается весь фреймворк (~3-4 MB) вместо нужных классов
- Дублирование CSS в разных шаблонах
- Нет минификации
- Нет purge неиспользуемых классов
- Медленная загрузка на production

### 3. Варианты оптимизации

**Вариант A: Standalone CLI (быстрый переход)**
- Плюс: не требует Node.js на production
- Плюс: простая настройка
- Плюс: автоматический purge
- Минус: требует запуск при разработке

**Вариант B: NPM + PostCSS (полный контроль)**
- Плюс: полный контроль над сборкой
- Плюс: интеграция с другими инструментами
- Минус: требует Node.js окружение

**Вариант C: django-tailwind пакет**
- Плюс: Django-native решение
- Плюс: автоматическая hot-reload
- Минус: дополнительная зависимость

## Оптимизация: Standalone CLI

### Шаг 1: Установка (Windows / PowerShell)

```powershell
Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe" -OutFile "tailwindcss.exe"
```

### Шаг 2: Создать tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4f46e5',
        secondary: '#10b981',
      }
    }
  },
  plugins: [],
}
```

### Шаг 3: Создать input.css

```css
/* static/src/tailwind.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Кастомные компоненты из <style> блоков */
@layer components {
  .domain-card {
    @apply transition-all duration-300;
  }

  .domain-card:hover {
    @apply -translate-y-1 shadow-xl;
  }
}
```

### Шаг 4: Сборка (PowerShell)

```powershell
# Development (watch mode)
.\tailwindcss.exe -i .\static\src\tailwind.css -o .\static\dist\tailwind.css --watch

# Production (minified)
.\tailwindcss.exe -i .\static\src\tailwind.css -o .\static\dist\tailwind.min.css --minify
```

### Шаг 5: Обновить base.html

```html
<!-- Заменить CDN на локальный файл -->
{% load static %}
<link rel="stylesheet" href="{% static 'dist/tailwind.min.css' %}">

<!-- Удалить: -->
<!-- <script src="https://cdn.tailwindcss.com"></script> -->
```

## Рефакторинг дублированных стилей

### Извлечение компонентов Tailwind

**До (дублирование в каждом файле):**

```html
<!-- templates/dashboard/index.html -->
<style>
  .domain-card { transition: all 0.3s ease; }
  .domain-card:hover { transform: translateY(-5px); }
</style>

<!-- templates/dashboard/domains.html -->
<style>
  .domain-card { transition: all 0.3s ease; }  <!-- Дублирование! -->
</style>
```

**После (централизовано в input.css):**

```css
@layer components {
  .domain-card {
    @apply transition-all duration-300 hover:-translate-y-1 hover:shadow-xl;
  }

  .btn-primary {
    @apply bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition;
  }
}
```

## Типичные паттерны рефакторинга

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

### Inline стили → Tailwind классы

**До:**
```html
<style>
  .custom-card {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
</style>
```

**После:**
```html
<div class="bg-white rounded-lg p-6 shadow-sm">
```

## Миграция: Пошаговый план (CDN → production)

### Фаза 1: Подготовка (без изменения работающего кода)
1. [ ] Установить Tailwind CLI
2. [ ] Создать `tailwind.config.js`
3. [ ] Создать `static/src/tailwind.css`
4. [ ] Собрать первую версию CSS
5. [ ] Проверить размер файла

### Фаза 2: Извлечение стилей
1. [ ] Найти все `<style>` блоки (Grep `<style>` по `templates/**/*.html`)
2. [ ] Перенести общие стили в `input.css` → `@layer components`
3. [ ] Пересобрать CSS и проверить

### Фаза 3: Обновление base template
1. [ ] В `base.html` заменить CDN на `{% static 'dist/tailwind.css' %}`
2. [ ] Удалить `<script>tailwind.config = ...</script>`
3. [ ] Протестировать на dev сервере

### Фаза 4: Очистка
1. [ ] Удалить все перенесенные `<style>` блоки из шаблонов
2. [ ] Финальная production сборка с `--minify`

### Фаза 5: Production deploy
1. [ ] `python manage.py collectstatic`
2. [ ] Обновить nginx для кеширования CSS (1 год)
3. [ ] Проверить размер загружаемых ресурсов (DevTools Network)

## Ожидаемый результат

```
До (CDN):
- tailwindcss CDN: ~3.5 MB
- Первая загрузка: ~4 секунды

После (optimized):
- tailwind.min.css: 30-80 KB (сжатый: 5-15 KB)
- Первая загрузка: ~0.5 секунды
- Кеширование: 1 год
```

## Чеклист перед production

- [ ] Все `<style>` блоки перенесены в `input.css`
- [ ] CDN скрипты удалены из шаблонов
- [ ] `tailwind.config.js` включает все пути к шаблонам
- [ ] CSS собран с флагом `--minify`
- [ ] Проверен размер финального CSS (должен быть < 50KB)
- [ ] Django `collectstatic` выполнен
