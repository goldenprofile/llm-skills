# Django Tailwind Optimizer — миграции и Legacy v3

## План миграции: CDN → v4 standalone (по фазам)

### Фаза 1: Подготовка (без изменения работающего кода)
1. [ ] Скачать standalone CLI v4 с зафиксированным тегом (см. SKILL.md, Шаг 1)
2. [ ] Создать `static/src/tailwind.css` (`@import "tailwindcss"` + `@source` + `@theme`)
3. [ ] Перенести палитру из `<script>tailwind.config = {...}</script>` (CDN-конфиг) в `@theme`
4. [ ] Собрать первую версию CSS, проверить размер файла

### Фаза 2: Извлечение стилей
1. [ ] Найти все `<style>` блоки (Grep `<style>` по `templates/**/*.html`)
2. [ ] Перенести общие стили в `input.css` → `@layer components`
3. [ ] Пересобрать CSS и проверить

### Фаза 3: Обновление base template
1. [ ] В `base.html` заменить CDN на `{% static 'dist/tailwind.min.css' %}`
2. [ ] Удалить `<script src="https://cdn.tailwindcss.com">` и inline `tailwind.config`
3. [ ] Протестировать на dev сервере — визуально сравнить ключевые страницы

### Фаза 4: Очистка
1. [ ] Удалить все перенесённые `<style>` блоки из шаблонов
2. [ ] Финальная production сборка с `--minify`

### Фаза 5: Production deploy
1. [ ] `python manage.py collectstatic`
2. [ ] Обновить nginx для кеширования CSS (1 год)
3. [ ] Проверить размер загружаемых ресурсов (DevTools Network)

## Апгрейд v3 → v4

Официальный инструмент: `npx @tailwindcss/upgrade` (нужен Node.js; прогоняется
один раз, результат коммитится — Node на проде не нужен). Ключевые изменения:

| v3 | v4 |
|---|---|
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` |
| `tailwind.config.js` → `content: [...]` | автообнаружение + `@source "путь";` |
| `theme.extend.colors` в JS | `@theme { --color-primary: ...; }` в CSS |
| `npx tailwindcss` (пакет `tailwindcss`) | `npx @tailwindcss/cli` или standalone-бинарь v4 |

- Старый `tailwind.config.js` можно временно подключить в v4 через
  `@config "../tailwind.config.js";` — как мост, не как постоянное решение.
- После апгрейда прогони сборку и сравни размер/вид ключевых страниц.

**Ограничение браузеров v4:** Safari 16.4+, Chrome 111+, Firefox 128+. Если
нужно поддерживать старее — оставайся на v3 (ветка Legacy ниже).

## Legacy: проект остаётся на v3

Рабочий v3-сетап не трогаем; правила те же, синтаксис другой.

### Установка standalone CLI v3 (Windows / PowerShell)

Фиксируй тег v3-линейки (последний — v3.4.x), НЕ `latest` (он отдаст v4):

```powershell
$v = "v3.4.17"
Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/$v/tailwindcss-windows-x64.exe" -OutFile "tailwindcss.exe"
```

### tailwind.config.js (обязателен в v3)

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

### input.css (v3-директивы)

```css
/* static/src/tailwind.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .domain-card {
    @apply transition-all duration-300 hover:-translate-y-1 hover:shadow-xl;
  }
}
```

### Сборка — те же флаги, что и v4

```powershell
.\tailwindcss.exe -i .\static\src\tailwind.css -o .\static\dist\tailwind.min.css --minify
```

`content` в конфиге обязан покрывать все шаблоны и python-код с классами —
иначе purge вырежет используемые классы.
