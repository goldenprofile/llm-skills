#!/usr/bin/env python3
"""
HTML-to-Markdown converter.

Primary engine: markdownify (pip install markdownify)
Fallback: stdlib HTMLParser (no external deps)

Usage:
    python html2md.py <input.html> [output.md] [--title "..." --source "..." --author "..." --tags "t1,t2"]

If output is omitted, prints to stdout.

Pipeline:
    1. Fetch HTML (done externally via curl)
    2. Extract <article> or .entry-content from full HTML page
    3. Strip noise (scripts, styles, nav, ads, social buttons) via regex
    4. Convert to Markdown (markdownify or stdlib fallback)
    5. Post-process: fix smart quotes, stray code fences, remove social junk
    6. Add YAML frontmatter (optional --title, --source, --author flags)

Designed for blog posts, documentation pages, and technical guides.
"""
import re
import sys
from html import unescape

# ─── Engine selection ──────────────────────────────────────────────────

# Try markdownify; if not found, manually add user site-packages and retry
# (helps when markdownify is installed in user site-packages but not on sys.path,
# e.g. when running under `python -S`)
HAS_MARKDOWNIFY = False
md_lib = None
try:
    import markdownify as md_lib
    HAS_MARKDOWNIFY = True
except ImportError:
    import sys as _sys
    import os as _os
    for _sp in [
        _os.path.join(_os.environ.get('APPDATA', ''), 'Python', 'Python313', 'site-packages'),
        'C:/Program Files/Python313/Lib/site-packages',
    ]:
        if _os.path.isdir(_sp) and _sp not in _sys.path:
            _sys.path.insert(0, _sp)
    try:
        import markdownify as md_lib
        HAS_MARKDOWNIFY = True
    except ImportError:
        pass


# ─── HTML cleaning ──────────────────────────────────────────────────────

def clean_html(html):
    """Remove script, style, nav, ads, and other noise before parsing."""
    for tag in ('script', 'style', 'svg', 'nav', 'noscript', 'iframe', 'form'):
        html = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove button blocks (copy buttons, share buttons)
    html = re.sub(r'<button[^>]*>.*?</button>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove ad containers
    html = re.sub(r'<div[^>]*class="[^"]*(?:advertisement|ad-container|ad-box|lc-nitropay)[^"]*"[^>]*>.*?</div>',
                  '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove ad-label spans
    html = re.sub(r'<span[^>]*class="[^"]*(?:lc-nitropay|ad-label|advertisement)[^"]*"[^>]*>.*?</span>',
                  '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return html


def extract_article(html):
    """Extract main article content from a full HTML page."""
    # Try .entry-content (common in WordPress / GeneratePress themes)
    m = re.search(r'<div class="entry-content"[^>]*>(.*)</div>\s*</div>\s*(?:<footer|</article|<div class="entry)',
                  html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    # Try <article> tag
    m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    # Try <main> tag
    m = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return html


# ─── markdownify engine ─────────────────────────────────────────────────

def convert_with_markdownify(html):
    """Convert HTML to Markdown using markdownify library."""
    # Configure markdownify for clean output
    md = md_lib.markdownify(
        html,
        heading_style='ATX',        # # style headings
        bullets='-',                 # - for unordered lists
        strip=['img'],               # skip images (often tracking pixels / ads)
        code_language='',            # no language hint on code blocks
        escape_asterisks=False,
        escape_underscores=False,
    )
    return md


# ─── stdlib fallback engine ─────────────────────────────────────────────

from html.parser import HTMLParser

class HTMLToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.in_pre = False
        self.in_code = False
        self.in_cell = False
        self.current_cell = []
        self.current_row = []
        self.table_rows = []
        self.link_href = None
        self.link_text_buf = []
        self.list_stack = []
        self.heading_level = 0
        self.heading_buf = []
        self.in_heading = False
        self.in_blockquote = False
        self.blockquote_buf = []

    def _emit(self, text):
        if self.in_cell:
            self.current_cell.append(text)
        elif self.link_href is not None:
            self.link_text_buf.append(text)
        elif self.in_heading:
            self.heading_buf.append(text)
        elif self.in_blockquote:
            self.blockquote_buf.append(text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.heading_level = int(tag[1])
            self.in_heading = True
            self.heading_buf = []
        elif tag == 'p':
            self.out.append('\n')
        elif tag == 'br':
            self._emit(' ')
        elif tag == 'hr':
            self.out.append('\n---\n')
        elif tag == 'pre':
            self.in_pre = True
            self.out.append('\n```\n')
        elif tag == 'code':
            self.in_code = True
            if not self.in_pre:
                self._emit('`')
        elif tag == 'blockquote':
            self.in_blockquote = True
            self.blockquote_buf = []
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i'):
            self._emit('*')
        elif tag == 'a':
            href = attrs_d.get('href', '')
            if href and not href.startswith('#') and not href.startswith('javascript'):
                self.link_href = href
                self.link_text_buf = []
        elif tag == 'ul':
            self.list_stack.append(('ul', 0))
            self._emit('\n')
        elif tag == 'ol':
            self.list_stack.append(('ol', 0))
            self._emit('\n')
        elif tag == 'li':
            if self.list_stack:
                ltype, cnt = self.list_stack.pop()
                cnt += 1
                self.list_stack.append((ltype, cnt))
                indent = '  ' * (len(self.list_stack) - 1)
                marker = f'{cnt}.' if ltype == 'ol' else '-'
                self._emit(f'\n{indent}{marker} ')
        elif tag == 'table':
            self.table_rows = []
        elif tag == 'tr':
            self.current_row = []
        elif tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = ''.join(self.heading_buf).strip()
            self.out.append('\n' + '#' * self.heading_level + ' ' + text + '\n')
            self.heading_level = 0
            self.in_heading = False
        elif tag == 'p':
            self.out.append('\n\n')
        elif tag == 'pre':
            self.in_pre = False
            self.out.append('\n```\n')
        elif tag == 'code':
            self.in_code = False
            if not self.in_pre:
                self._emit('`')
        elif tag == 'blockquote':
            self.in_blockquote = False
            bq = ''.join(self.blockquote_buf).strip()
            bq = re.sub(r'\n+', '\n', bq)
            self.out.append('\n> ' + bq.replace('\n', '\n> ') + '\n')
            self.blockquote_buf = []
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i'):
            self._emit('*')
        elif tag == 'a':
            if self.link_href is not None:
                text = ''.join(self.link_text_buf).strip()
                href = self.link_href
                self.link_href = None
                self.link_text_buf = []
                if text:
                    self._emit(f'[{text}]({href})')
        elif tag in ('ul', 'ol'):
            if self.list_stack:
                self.list_stack.pop()
            self._emit('\n')
        elif tag in ('td', 'th'):
            cell = ''.join(self.current_cell).strip()
            cell = re.sub(r'\s+', ' ', cell)
            self.current_row.append(cell)
            self.in_cell = False
            self.current_cell = []
        elif tag == 'tr':
            self.table_rows.append(self.current_row)
            self.current_row = []
        elif tag == 'table':
            if self.table_rows:
                self.out.append('\n')
                for i, row in enumerate(self.table_rows):
                    if row:
                        self.out.append('| ' + ' | '.join(row) + ' |\n')
                        if i == 0:
                            self.out.append('| ' + ' | '.join(['---'] * len(row)) + ' |\n')
                self.out.append('\n')
                self.table_rows = []

    def handle_data(self, data):
        if self.in_pre or self.in_code:
            self._emit(data)
            return
        text = re.sub(r'\s+', ' ', data)
        self._emit(text)

    def get_markdown(self):
        text = ''.join(self.out)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        return text.strip()


def convert_with_stdlib(html):
    """Fallback: convert HTML to Markdown using only stdlib HTMLParser."""
    parser = HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


# ─── Post-processing ────────────────────────────────────────────────────

def post_process(md):
    """Clean up common conversion artifacts and remove social junk."""
    # Fix replacement chars (broken smart quotes / encoding issues)
    md = md.replace('\ufffd', "'")
    # Remove stray lone backtick lines (artifact from inline <code> near <pre>)
    md = re.sub(r'\n`\s*\n', '\n', md)
    md = re.sub(r'\n``\s*\n', '\n', md)
    # Fix missing opening backtick: "use sudo`." -> "use `sudo`."
    md = re.sub(r'(\s)(sudo|pg_dump|pg_dumpall)`', r'\1`\2`', md)
    # Remove empty code blocks
    md = re.sub(r'```\s*```', '', md)
    # Remove stray opening code fence followed by blockquote
    md = re.sub(r'```\n\n+>', '>', md)
    # Cut social/share/footer junk — common patterns across blog sites
    social_markers = [
        '  Share this guide', 'Share this guide',
        'Want more', '## Need another guide?',
        'Found this guide useful?', 'Support LinuxCapable',
        'Buy me a coffee', 'Add LinuxCapable',
        'Follow LinuxCapable', 'Share this article',
        'Was this post helpful', 'Related Posts',
    ]
    for marker in social_markers:
        idx = md.find(marker)
        if idx > 0:
            md = md[:idx].rstrip()
    # Remove "Add as preferred source" badges
    md = re.sub(r'\[!\[Add.*?\)\]', '', md)
    # Remove orphaned "Search" text
    md = re.sub(r'\nSearch \w+\s*$', '', md)
    # Remove "Categories" line
    md = re.sub(r'\n\s*Categories.*?\n', '\n', md)
    # Collapse excessive blank lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    # Remove trailing whitespace on lines
    md = re.sub(r'[ \t]+\n', '\n', md)
    return md.strip() + '\n'


# ─── Frontmatter ────────────────────────────────────────────────────────

def add_frontmatter(md, title='', source='', author='', site='', tags=None):
    """Add YAML frontmatter for Obsidian."""
    if not title:
        return md
    tags_str = ', '.join(tags) if tags else ''
    lines = ['---']
    lines.append(f'title: "{title}"')
    if source:
        lines.append(f'source: "{source}"')
    if author:
        lines.append(f'author: "{author}"')
    if site:
        lines.append(f'site: "{site}"')
    if tags_str:
        lines.append(f'tags: [{tags_str}]')
    # Use actual date
    from datetime import date
    lines.append(f'clipped: "{date.today().isoformat()}"')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines) + '\n' + md


# ─── Main ───────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description='Convert HTML to Markdown')
    ap.add_argument('input', help='Input HTML file')
    ap.add_argument('output', nargs='?', help='Output .md file (default: stdout)')
    ap.add_argument('--title', default='', help='Title for YAML frontmatter')
    ap.add_argument('--source', default='', help='Source URL for frontmatter')
    ap.add_argument('--author', default='', help='Author for frontmatter')
    ap.add_argument('--site', default='', help='Site name for frontmatter')
    ap.add_argument('--tags', default='', help='Comma-separated tags')
    args = ap.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html = f.read()

    article = extract_article(html)
    article = clean_html(article)

    if HAS_MARKDOWNIFY:
        md = convert_with_markdownify(article)
    else:
        md = convert_with_stdlib(article)

    md = post_process(md)

    if args.title:
        tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else None
        md = add_frontmatter(md, args.title, args.source, args.author, args.site, tags)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(md)
        engine = 'markdownify' if HAS_MARKDOWNIFY else 'stdlib'
        print(f"Written {len(md)} chars to {args.output} (engine: {engine})", file=sys.stderr)
    else:
        print(md)


if __name__ == '__main__':
    main()
