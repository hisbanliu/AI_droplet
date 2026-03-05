"""
fetch_news.py
Fetches AI-related news from RSS feeds, scores them with Gemini,
and writes the top results to data/news.json.
"""

import json
import os
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import httpx
from dotenv import load_dotenv

# ── Config ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_FILE = ROOT / "data" / "news.json"
TOP_N = 10          # how many articles to keep
HOURS_BACK = 36     # look back window (36h gives buffer for timezone drift)

RSS_FEEDS = [
    {"name": "OpenAI Blog",         "url": "https://openai.com/blog/rss.xml"},
    {"name": "Anthropic Blog",      "url": "https://www.anthropic.com/blog/rss.xml"},
    {"name": "Google DeepMind",     "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Google AI Blog",      "url": "https://blog.research.google/feeds/posts/default"},
    {"name": "TechCrunch AI",       "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI",        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "VentureBeat AI",      "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "arXiv cs.AI",         "url": "http://rss.arxiv.org/rss/cs.AI"},
    {"name": "Hugging Face Blog",   "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Tech Review AI",  "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
]

SCORING_PROMPT = """You are an AI news curator. Given a list of article titles and snippets, 
score each for importance to AI/ML practitioners (0-10) and write a one-sentence English summary.

Rules:
- Score 9-10: Major model releases, breakthrough research, industry-changing announcements
- Score 7-8: Significant product launches, notable research papers, important company news
- Score 5-6: Interesting tools, minor updates, opinion pieces worth reading
- Score 0-4: Tangential, repetitive, or low-signal content

Return a JSON array with this structure for each article:
[{"index": 0, "score": 8.5, "summary_en": "...", "summary_zh": "..."}]

Only include articles with score >= 5.
Keep summary_en under 120 characters, summary_zh under 50 characters.

Articles:
{articles}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_id(url: str, date: str) -> str:
    return hashlib.md5(f"{url}{date}".encode()).hexdigest()[:12]


def parse_date(entry) -> datetime | None:
    """Try to extract a timezone-aware datetime from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(feed_cfg: dict, cutoff: datetime) -> list[dict]:
    """Fetch one RSS feed, return articles newer than cutoff."""
    articles = []
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        for entry in parsed.entries:
            pub = parse_date(entry)
            if pub and pub < cutoff:
                continue  # too old
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", ""))[:500]
            if not title or not link:
                continue
            articles.append({
                "source": feed_cfg["name"],
                "title": title,
                "url": link,
                "published_at": pub.isoformat() if pub else datetime.now(timezone.utc).isoformat(),
                "snippet": summary,
            })
    except Exception as e:
        print(f"  [WARN] {feed_cfg['name']}: {e}", file=sys.stderr)
    return articles


def _fallback_scores(articles):
    return [{"index": i, "score": 6.0, "summary_en": a["title"], "summary_zh": a["title"]}
            for i, a in enumerate(articles)]


def _call_gemini(prompt: str, api_key: str) -> list:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)


def _call_openai_compat(prompt: str, api_key: str, base_url: str, model: str) -> list:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    # The prompt asks for a JSON array; wrap in object if needed
    text = response.choices[0].message.content
    parsed = json.loads(text)
    # Handle both {"results": [...]} and [...] responses
    return parsed if isinstance(parsed, list) else next(
        (v for v in parsed.values() if isinstance(v, list)), [])


def score_with_ai(articles: list[dict]) -> list[dict]:
    """Send articles to the configured AI provider for importance scoring.

    Supports two providers via .env:
      AI_PROVIDER=gemini   (default) → uses GEMINI_API_KEY
      AI_PROVIDER=openai            → uses AI_API_KEY + AI_BASE_URL + AI_MODEL
                                       (works for OpenAI, DeepSeek, Kimi, Qwen, etc.)
    """
    provider = os.getenv("AI_PROVIDER", "gemini").lower()

    formatted = "\n".join(
        f'{i}. [{a["source"]}] {a["title"]}\n   {a["snippet"][:200]}'
        for i, a in enumerate(articles)
    )
    prompt = SCORING_PROMPT.replace("{articles}", formatted)

    try:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set")
            scores = _call_gemini(prompt, api_key)
        else:  # openai-compatible: OpenAI, DeepSeek, Kimi, Qwen, etc.
            api_key = os.getenv("AI_API_KEY")
            base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
            model = os.getenv("AI_MODEL", "gpt-4o-mini")
            if not api_key:
                raise ValueError("AI_API_KEY not set")
            scores = _call_openai_compat(prompt, api_key, base_url, model)
    except Exception as e:
        print(f"[WARN] AI scoring failed ({provider}): {e} – using fallback.", file=sys.stderr)
        scores = _fallback_scores(articles)

    # Merge scores back
    scored = []
    for s in scores:
        idx = s.get("index", -1)
        if 0 <= idx < len(articles):
            a = articles[idx].copy()
            a["importance_score"] = round(float(s.get("score", 5.0)), 1)
            a["summary_en"] = s.get("summary_en", a["title"])[:150]
            a["summary_zh"] = s.get("summary_zh", "")[:80]
            scored.append(a)

    scored.sort(key=lambda x: x["importance_score"], reverse=True)
    return scored[:TOP_N]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== fetch_news.py ===")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    print(f"Fetching articles since {cutoff.strftime('%Y-%m-%d %H:%M')} UTC")

    all_articles = []
    for feed in RSS_FEEDS:
        items = fetch_rss(feed, cutoff)
        print(f"  {feed['name']}: {len(items)} articles")
        all_articles.extend(items)

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    print(f"Total unique articles: {len(unique)}")

    if not unique:
        print("[WARN] No articles found. Keeping existing news.json.")
        return

    provider = os.getenv("AI_PROVIDER", "gemini")
    print(f"Scoring top articles with AI ({provider})...")
    top = score_with_ai(unique)

    # Add unique IDs and clean up
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i, a in enumerate(top):
        a["id"] = f"{today}-{make_id(a['url'], a['published_at'])}"
        a.pop("snippet", None)

    OUTPUT_FILE.write_text(json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(top)} articles to {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
