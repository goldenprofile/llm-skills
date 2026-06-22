---
name: obsidian-clippings
description: Ingest shared content (URLs, articles, forwarded messages, pasted snippets) into an Obsidian vault as structured Markdown with YAML frontmatter and media attachments.
tags: [obsidian, clippings, inbox, articles]
---

# Obsidian Clippings

Save shared content (article URLs, forwarded messages, pasted snippets) from any
channel into the vault as structured Markdown notes with metadata and media.

## Trigger

- User shares/forwards content and asks to save it
- User sends a URL (article, GitHub repo, blog) to capture
- User says "сохрани" / "запиши" in the context of shared content

## Where it goes

Save clippings under the vault's inbox zone (see SKILL.md → "Структура папок"):
`<vault>/inbox/` (or your vault's equivalent, e.g. `1-INBOX/`), media under
`<vault>/attachments/`. Resolve the vault root per SKILL.md → "Путь к хранилищу".

## Workflow

1. **Receive** the content (text + any media)
2. **Verify date** — use today's actual date (see SKILL.md → "Дата")
3. **Extract** key info: source, main topic, notable quotes
4. **Generate** a concise title and relevant tags from the content
5. **Save media** — copy any images/files into `<vault>/attachments/`
6. **Write note** — `Write` a Markdown file with YAML frontmatter using the verified date

## Note Format

**Filename:** `YYYY-MM-DD - Short Title.md`

**Template:**
```markdown
---
title: "Descriptive Title"
date: YYYY-MM-DD
source: URL | Channel name | Shared
tags: [tag1, tag2, tag3]
media:
  - "![[filename.ext]]"
---

# Title

[Structured body with headings, quotes in blockquotes, key points as bullet lists]
```

### Frontmatter Fields
- `title` — concise descriptive title (match the content language)
- `date` — date of the clipping
- `source` — origin: URL, channel name, "Shared", etc.
- `tags` — auto-generated from content analysis (3-7 tags)
- `media` — list of attachments using Obsidian embed syntax: `- "![[filename.ext]]"`

### Body Guidelines
- Use headings to structure long content
- Put notable quotes in `>` blockquotes with attribution
- Keep the original voice — don't paraphrase the author's intent
- Add brief context if the shared content is incomplete without it
- Write in the language of the original content

## Media Handling

1. Identify media from the source (images, videos, PDFs)
2. Copy the file into `<vault>/attachments/`
3. Reference it in frontmatter with the vault-relative path
4. For inline display, use `![[filename.ext]]` in the body where appropriate
5. **Extract structured data from images**: when an image holds tables, benchmarks,
   metrics, or dashboard data, transcribe the key data into the note body as a
   markdown table or list. The note should be useful without opening the attachment.
   Keep the `![[image]]` embed for visual reference.
6. **Reconcile label mismatches**: when image labels differ from the accompanying
   text (e.g. image says "M5" but text says "MiniMax M3"), trust the text for primary
   naming and note the discrepancy briefly if it matters. Don't silently override the
   user's text.

## Tags

Auto-generate from content analysis:
- 3-7 tags per clipping
- lowercase, hyphenated (e.g. `claude-code`, `ai-agents`)
- prefer broad-but-relevant over hyper-specific
- common clusters: `ai`, `education`, `tools`, `startup`, `career`, `design`,
  `security`, `productivity`

## Finding the Vault

If the vault path is unknown, auto-detect it with `Glob` for `**/.obsidian` — that
folder marks the root of every vault. Otherwise ask the user.

## Templates

- `templates/clipping.md` — starter Markdown template with frontmatter placeholders

## Batch Processing

When multiple clippings arrive in one message (text + images on different topics),
split them into **separate notes** — one per topic, each with its own file,
frontmatter, and tags.

For large batches, process sequentially and methodically — accuracy over speed.

### Multi-topic message signals
- Two or more distinct subjects with no logical connection
- Separate images that belong to different topics
- "Also" / "Ещё" / line breaks between unrelated paragraphs

### Batch GitHub repos (3+ URLs)

When the user sends multiple GitHub repo URLs, fan out with the `Agent` tool (one
subagent per repo, run concurrently). Each subagent:
1. Fetches repo metadata: `https://api.github.com/repos/{owner}/{repo}`
2. Fetches the raw README: `https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/README.md`
3. Translates key sections (description, features, installation, usage) to Russian if
   the README is not in Russian
4. Returns structured data: stars, language, license, last update, translated content

The parent then writes all clipping files from the returned data. See
`references/github-extraction.md` for the full pattern.

## Technical Clippings

When a clipping contains **code, config, or CLI commands**, preserve them in fenced
code blocks with the right language tag. Copy technical content verbatim — don't
paraphrase or reformat. Applies to config snippets (TOML/YAML/JSON), CLI commands and
flags, API endpoints and parameters.

## URL Handling (Articles, GitHub Repos, Blogs)

When the user sends a URL (with or without commentary), extract its content and save
it as a clipping.

### Workflow

1. **Fetch** the page content with `WebFetch` (or `curl` for raw HTML)
2. **For GitHub repos** — also fetch metadata via the GitHub API
   (`https://api.github.com/repos/{owner}/{repo}`: stars, language, license, last update)
   and the raw README from `raw.githubusercontent.com`
3. **Translate** if the original is not in Russian — translate key sections into the
   note body
4. **Save media** — any screenshots/images go to `<vault>/attachments/`
5. **Write note** — same format as regular clippings; `source` holds the URL

### Source field format for URLs
- Articles: the URL (e.g. `https://habr.com/ru/articles/12345/`)
- GitHub: `Shared — https://github.com/owner/repo`

### Content extraction tips
- **Habr, Medium, blogs**: `WebFetch` usually returns the main article text
- **GitHub README**: fetch from `raw.githubusercontent.com` directly
- **Paywalled / Cloudflare-protected sites**: challenges block both `WebFetch` and
  `curl` — you'll see "Just a moment..." or a security-check page. Fallback: save a
  minimal stub note with the URL and `⚠️ Сайт защищён Cloudflare`, then ask the user
  for a screenshot or pasted text.
- **JS-heavy SPAs**: may need real browser automation — use the `agent-browser` skill
  or Playwright MCP if connected.

### Quality HTML→Markdown conversion (technical articles, guides, docs)

When the user asks for a **quality** conversion ("качественно конвертировать"), plain
text extraction is insufficient — it strips formatting (code blocks, tables, headings,
links). Use the full HTML→Markdown pipeline instead.

**Pipeline** (`markdownify` used if installed; stdlib fallback is automatic):

1. **Fetch HTML** via curl:
   `curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "URL" -o page.html`
2. **Convert** using the skill's converter (run from the skill directory):
   ```bash
   python scripts/html2md.py page.html out.md \
     --title "Article Title" --source "URL" --author "Author" --site "SiteName" \
     --tags "tag1,tag2,tag3"
   ```
3. **Review** the output — check for stray code fences, broken tables, missing links
4. **Save** to the appropriate vault folder

**If Python fails to start** (a broken `.pth` in user site-packages can crash
`site.py` on some hosts): run with `python -S` to skip `site.py`. Set `PYTHONUTF8=1`
to avoid smart-quote encoding issues. The script auto-detects `markdownify` and falls
back to stdlib if it's unavailable.

The converter (`scripts/html2md.py`) handles:
- Engine: tries `markdownify`, falls back to stdlib `HTMLParser`
- Extracting `<article>` / `.entry-content` from full pages
- Stripping ads, scripts, nav, social-share buttons
- Converting headings, code blocks, tables, links, blockquotes, lists, inline formatting
- Fixing smart quotes, stray code fences, social junk
- Adding YAML frontmatter via `--title`, `--source`, `--author`, `--site`, `--tags`

**When plain extraction is fine vs the full pipeline**:
- `WebFetch` / `innerText` → quick clippings where formatting doesn't matter
- Full pipeline → technical guides with code/commands, articles with tables, anything
  the user calls "качественно"

### Translation

When the source is in English (or another non-Russian language):
- Translate the key sections into Russian in the note body
- Keep original terms/names in parentheses where helpful (e.g. «уровень размышления
  (thinking level)»)
- Keep code examples, commands, and technical terms untranslated
- Note the original-language title if it differs from the Russian one

## PDF Extraction

When the user sends a PDF:
1. Read it directly with `Read` (it supports PDFs) and extract the text/structure
2. Copy the PDF into `<vault>/attachments/` and reference it with `![[filename.pdf]]`
3. For scanned/garbled PDFs, fall back to vision: ask the user for a screenshot or use
   the `agent-browser` skill to open and capture pages

## Pitfalls

- **Missing links**: preserve any URLs the original content contained — add a
  `## Ссылки` section at the bottom or inline them contextually. Don't lose references.
- **Wrong date**: the date in the filename AND the frontmatter must be today's actual
  date (see SKILL.md → "Дата"). The #1 recurring mistake is reusing a stale date.
- **Cloudflare-protected sites**: many sites block automation. Save a stub with the URL
  and ask the user for a screenshot or text paste.
- **Obsidian wikilinks**: `[[Note Name]]` for inter-note links; `![[file.ext]]` for
  inline attachments.
- **Don't overwrite**: check whether a clipping with the same date+title already exists
  before writing.
