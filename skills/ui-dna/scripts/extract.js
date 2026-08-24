// ui-dna — извлечение визуального языка страницы из живого DOM.
//
// Файл целиком — одно арроу-выражение: передаётся как есть в
// playwright `browser_evaluate({function: <содержимое файла>})` либо в
// claude-in-chrome `javascript_tool`. Возвращает агрегат ~4-6 КБ,
// а НЕ подеревный дамп: агрегация делается здесь, в браузере, иначе
// 4000+ элементов выжигают контекст.
() => {
  // Имена вида --sx-1urpf9d генерирует сборщик; смысла в них нет.
  const HASH = /^--(sx|css|tw|ch|emotion|jsx?)-[a-z0-9]{5,}$/i;
  const VIEW = innerWidth * innerHeight;

  const px = v => { const n = parseFloat(v); return Number.isFinite(n) ? Math.round(n) : null; };
  // border-radius: 50% приходит как "50%" — parseFloat дал бы 50px.
  const rad = v => { if (!v) return null; if (v.includes('%')) return 9999;
                     const n = px(v); return n ? (n > 100 ? 9999 : n) : null; };
  const norm = c => {
    if (!c || c === 'none') return null;
    const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if (p.length >= 4 && p[3] === 0) return null;          // полностью прозрачное — не цвет
    const h = n => n.toString(16).padStart(2, '0');
    return '#' + h(p[0]) + h(p[1]) + h(p[2]) +
           (p.length >= 4 && p[3] < 1 ? h(Math.round(p[3] * 255)) : '');
  };
  const bump = (m, k, w) => { if (k != null) m.set(k, (m.get(k) || 0) + w); };
  const top = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n)
                          .map(([k, v]) => [k, Math.round(v)]);

  const bg = new Map(), fg = new Map(), bd = new Map(), fam = new Map(), size = new Map(),
        weight = new Map(), lh = new Map(), radius = new Map(), pad = new Map(),
        gap = new Map(), shadow = new Map(), comp = new Map();

  const CTRL = 'button,[role=button],input:not([type=hidden]),select,textarea,.btn';
  const all = [...document.querySelectorAll('body *')];
  const els = all.slice(0, 4000);
  let scanned = 0, maxW = 0;

  for (const el of els) {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') continue;
    scanned++;

    // Вес по площади: полноэкранный фон должен перевесить 200 мелких span.
    const area = Math.min(r.width * r.height, VIEW) / 1000;
    // Вес типографики — по объёму текста, а не по числу узлов.
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const txt = Math.min((el.textContent || '').trim().length, 400);

    const mw = px(s.maxWidth); if (mw > 400 && mw < 2000) maxW = Math.max(maxW, mw);

    bump(bg, norm(s.backgroundColor), area);
    if (own) {
      bump(fg, norm(s.color), txt);
      bump(fam, s.fontFamily.split(',')[0].replace(/["']/g, '').trim(), txt);
      bump(size, px(s.fontSize), txt);
      bump(weight, s.fontWeight, txt);
      const l = parseFloat(s.lineHeight) / parseFloat(s.fontSize);
      if (Number.isFinite(l)) bump(lh, l.toFixed(2), txt);
    }
    if (px(s.borderTopWidth)) bump(bd, norm(s.borderTopColor), area);
    bump(radius, rad(s.borderTopLeftRadius), 1);
    for (const p of [s.paddingTop, s.paddingLeft]) { const v = px(p); if (v) bump(pad, v, 1); }
    const g = px(s.rowGap ?? s.gap); if (g) bump(gap, g, 1);
    if (s.boxShadow && s.boxShadow !== 'none') bump(shadow, s.boxShadow.slice(0, 60), 1);

    // Компоненты — не по классам (у Tailwind/CSS-in-JS они бессмысленны),
    // а по сигнатуре стиля: одинаковая сигнатура = один вариант компонента.
    if (el.matches(CTRL)) {
      bump(comp, [el.tagName.toLowerCase(), norm(s.backgroundColor), norm(s.color),
                  rad(s.borderTopLeftRadius), s.padding, s.fontWeight,
                  px(s.borderTopWidth) ? norm(s.borderTopColor) : 'no-border'].join(' | '), 1);
    }
  }

  // CSS-переменные читаем из computed style, а НЕ обходом document.styleSheets:
  // у кросс-доменных таблиц .cssRules бросает SecurityError (на linear.app
  // так недоступны 51 из 85 таблиц), и computed-путь при этом полнее.
  const cs = getComputedStyle(document.documentElement), vars = {};
  for (const p of cs) if (p.startsWith('--') && !HASH.test(p)) {
    const v = cs.getPropertyValue(p).trim();
    if (v && v.length < 40) vars[p] = v;
  }

  const hdr = document.querySelector('header,[role=banner]');
  const scheme = cs.getPropertyValue('color-scheme').trim();

  return {
    site: location.hostname, path: location.pathname,
    viewport: [innerWidth, innerHeight],
    scanned, domTotal: all.length, truncated: all.length > 4000,
    colorScheme: scheme || null,
    background: top(bg, 8), text: top(fg, 6), border: top(bd, 5),
    fontFamily: top(fam, 4), fontSize: top(size, 8), fontWeight: top(weight, 5),
    lineHeight: top(lh, 4),
    radius: top(radius, 6), padding: top(pad, 10), gap: top(gap, 6), shadow: top(shadow, 4),
    layout: { maxContentWidth: maxW || null,
              headerHeight: hdr ? Math.round(hdr.getBoundingClientRect().height) : null },
    cssVars: { count: Object.keys(vars).length,
               sample: Object.entries(vars).slice(0, 40).map(([k, v]) => k + ': ' + v) },
    components: top(comp, 8)
  };
}
