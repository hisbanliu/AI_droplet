# Changelog

All notable changes to AI Droplet are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]
_Planned for future versions_
- GitHub Actions cron job for fully automated daily updates (v2)
- User-facing comments via Giscus (v3)
- Migration to Next.js + Vercel with SSR and user accounts (v4)
- LMSYS Chatbot Arena benchmark leaderboard section
- Benchmark comparison table for models

---

## [0.1.0] — 2026-03-04

### Added
- Project scaffold: `scripts/`, `data/`, `templates/`, `static/`, `docs/`
- **`scripts/fetch_news.py`**: Fetches AI news from 10 RSS feeds (OpenAI, Anthropic,
  Google DeepMind, TechCrunch, The Verge, VentureBeat, arXiv cs.AI, HuggingFace Blog,
  MIT Tech Review, Hacker News). Uses Gemini API to score (0–10) and summarize top 10 articles.
- **`scripts/fetch_models.py`**: Pulls top-liked open-source models from HuggingFace API
  (`sort=likes`; note: HuggingFace REST API no longer supports `sort=trending`),
  merges with hand-curated commercial models. Deduplicates by `huggingface_id`.
- **`scripts/fetch_mcp.py`**: Fetches and parses the `punkpeye/awesome-mcp-servers` GitHub
  README to build a structured MCP server directory.
- **`scripts/generate_site.py`**: Renders all JSON data into `docs/index.html` via Jinja2.
- **`run_daily.py`**: One-click runner with `--push`, `--skip-news`, `--skip-models`,
  `--skip-mcp` flags.
- **`templates/index.html.j2`**: Single-page responsive UI (Tailwind CSS + Alpine.js).
  Sections: Daily News, Models, MCP, Agent Skills, AI IDEs, AI Tools.
  Features: EN/中 language toggle, model search + type filter + pagination,
  MCP category filter + search, tools category tabs.
- **`static/i18n.js`**: Source-of-truth translation file (embedded at build time).
- **`data/models_curated.json`**: 17 hand-curated models (GPT-4o, o3, Claude 3.7 Sonnet,
  Gemini 2.0 Flash, Grok 3, Llama 4, DeepSeek-R1, Mistral, Qwen2.5, Phi-4, Gemma 3).
- **`data/skills.json`**: 15 Anthropic Agent Skills (hand-curated).
- **`data/ides.json`**: 8 AI IDEs (VS Code+Copilot, Cursor, Windsurf, Zed, JetBrains AI,
  Replit, Devin, Void).
- **`data/tools.json`**: 18 AI tools across 6 categories (image gen, video gen, audio,
  search, coding, productivity).
- **`PLAN.md`**: Full project plan with architecture, data sources, i18n spec, JSON schemas,
  and v1–v4 upgrade roadmap.
- **`CHANGELOG.md`**: This file.
- GitHub Pages deployment configured to `docs/` directory.

### Technical decisions recorded
- Static site (GitHub Pages) chosen over server-based hosting for zero maintenance cost
  while in manual-update phase.
- Gemini `gemini-2.0-flash` chosen for AI scoring due to high free-tier quota.
- `docs/` chosen as Pages source to keep source code and build output in same branch.
- Translations embedded inline in generated HTML (not referenced as external JS) for
  single-file portability.

---

_Older entries will appear here as versions are released._
