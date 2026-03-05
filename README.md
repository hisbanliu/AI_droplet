# AI Droplet

> 你的每日 AI 情报站 · Your Daily AI Intelligence

A static aggregation site covering AI news, models, tools, MCP servers, and agent skills — updated daily and hosted on GitHub Pages.

**Live site →** https://hisbanliu.github.io/AI_droplet/

---

## Contents

| Section | Source | Update |
|---------|--------|--------|
| Daily News | 10 RSS feeds → Gemini scoring, Top 10 | Daily |
| Models | HuggingFace API + curated commercial models | Daily |
| MCP Servers | `punkpeye/awesome-mcp-servers` README (1 294 servers) | Weekly |
| Agent Skills | Anthropic — curated | Manual |
| AI IDEs | Curated (8 IDEs) | Manual |
| AI Tools | Curated (32 tools, 8 categories) | Manual |

Languages: **EN / 中文** toggle, preference saved to `localStorage`.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/hisbanliu/AI_droplet.git
cd AI_droplet

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Dependencies
pip install -r requirements.txt

# 4. API keys
cp .env.example .env
# Edit .env — add GEMINI_API_KEY and GITHUB_TOKEN

# 5. Run
python run_daily.py
# Opens http://localhost:8000 is NOT needed — just open docs/index.html in a browser,
# or push to GitHub and view the Pages URL.
```

`run_daily.py` accepts flags:

| Flag | Effect |
|------|--------|
| `--push` | `git add`, `git commit`, `git push` automatically |
| `--skip-news` | Skip news fetch (save API quota) |
| `--skip-models` | Skip HuggingFace fetch |
| `--skip-mcp` | Skip MCP README fetch |

---

## Architecture

```
Python scripts (scripts/)
    ├── fetch_news.py     →  data/news.json        (RSS + Gemini scoring)
    ├── fetch_models.py   →  data/models.json       (HuggingFace + curated)
    ├── fetch_mcp.py      →  data/mcp.json          (GitHub README parse)
    └── generate_site.py  →  docs/index.html        (Jinja2 render)
                             docs/data/*.json        (copied for fetch())

GitHub Pages (docs/)
    └── index.html ← 41 KB shell, loads data at runtime via fetch()
```

Templates are split for maintainability:

```
templates/
  index.html.j2          ← skeleton (head / nav / hero / footer / scripts)
  sections/
    news.html.j2          ← // 01 Daily News
    models.html.j2        ← // 02 Models
    mcp.html.j2           ← // 03 MCP Servers
    skills.html.j2        ← // 04 Agent Skills
    ides.html.j2          ← // 05 AI IDEs
    tools.html.j2         ← // 06 AI Tools
```

---

## Adding Tools

Edit `data/tools.json` — append an entry:

```json
{
  "name": "Tool Name",
  "category": "coding",
  "company": "Company",
  "description": "One-line description in English.",
  "url": "https://example.com",
  "pricing": "Free tier + $20/mo",
  "tags": ["tag1", "tag2"]
}
```

Existing categories: `image-generation` · `video-generation` · `audio` · `ai-search` · `coding` · `productivity` · `ai-agents` · `writing`

**Adding a new category:** add entries with a new `category` value, then add the i18n key `tools.cat.<category>` in both `en` and `zh` blocks inside `templates/index.html.j2`.  The frontend derives tab buttons automatically from the data.

---

## Environment Variables

```bash
# .env (local only — never committed)
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_pat_here    # optional — raises API rate limit 60 → 5000 req/h
```

---

## Tech Stack

- **Runtime**: Python 3.12, feedparser, httpx, Jinja2, google-generativeai
- **Frontend**: HTML + [Tailwind CSS](https://tailwindcss.com/) CDN + [Alpine.js](https://alpinejs.dev/) CDN
- **Fonts**: Fira Code + Inter (Google Fonts)
- **Hosting**: GitHub Pages (`docs/` directory, same branch)
- **AI**: Gemini 2.0 Flash (news scoring & summarization)

---

## Roadmap

See [PLAN.md](PLAN.md) for the full v1–v4 upgrade roadmap and v2 architecture design (manifest-driven section registry, i18n file extraction, GitHub Actions automation).
