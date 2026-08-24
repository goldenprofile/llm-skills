# GitHub Repo Extraction Pattern

## Single repo

1. Fetch metadata: `https://api.github.com/repos/{owner}/{repo}` (via `WebFetch` or `curl`)
   - Returns: `stargazers_count`, `language`, `license.spdx_id`, `updated_at`,
     `default_branch`, `description`
2. Fetch the raw README: `https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/README.md`
3. If the README is not in Russian, translate the key sections: description, features,
   installation, usage
4. Save any hero image from the README to the attachments zone (if accessible)
5. `Write` a clipping with a metadata header: `⭐ N | Language | License | Обновлён: date | URL`

## Batch (3+ repos) via subagents

Fan out with the `Agent` tool — one subagent per repo, run concurrently (send them in a
single message). Each subagent's task:

```
Fetch the README from https://github.com/{owner}/{repo} and return its full content.
Also note: stars, language, license, last update date. If the README is not in Russian,
provide a Russian translation of the key sections (description, features, installation,
usage). Return everything as structured text. Respond in Russian.
```

Each subagent:
- Fetches the raw README via `WebFetch`:
  `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md`
- Fetches metadata via `WebFetch`: `https://api.github.com/repos/{owner}/{repo}` and parses the JSON
- Returns ALL extracted data in its final message — the parent needs it to write files

The parent then:
1. Receives the structured data from all subagents
2. `Write`s the clipping files one by one

## Extraction fallbacks

If `raw.githubusercontent.com` fails or the branch isn't `main`:
- `WebFetch` the GitHub repo page directly
- If the page is JS-heavy and `WebFetch` returns too little, use Playwright MCP or
  Claude-in-Chrome (if connected) to render and extract

## Metadata format for the clipping header

```
⭐ {stars} | {language} | {license} | Обновлён: {date} | {homepage_url}
```

## Translation rules

- Description → Russian
- Features list → Russian, keep feature emoji prefixes
- Installation → keep commands untranslated, translate comments/explanations
- Usage → keep commands/code untranslated, translate prose
- Keep original English terms in parentheses where ambiguous (e.g. «уровень размышления
  (thinking level)»)
- Tags stay in English (lowercase, hyphenated)
