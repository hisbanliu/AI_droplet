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
import google.generativeai as genai

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


def score_with_gemini(articles: list[dict]) -> list[dict]:
    """Send articles to Gemini for importance scoring and summarization."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARN] GEMINI_API_KEY not set – skipping AI scoring, using all articles.", file=sys.stderr)
        for i, a in enumerate(articles[:TOP_N]):
            a["importance_score"] = 7.0
            a["summary_en"] = a["title"]
            a["summary_zh"] = a["title"]
        return articles[:TOP_N]

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    formatted = "\n".join(
        f'{i}. [{a["source"]}] {a["title"]}\n   {a["snippet"][:200]}'
        for i, a in enumerate(articles)
    )
    prompt = SCORING_PROMPT.format(articles=formatted)

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        scores = json.loads(response.text)
    except Exception as e:
        print(f"[ERROR] Gemini scoring failed: {e}", file=sys.stderr)
        scores = [{"index": i, "score": 6.0, "summary_en": a["title"], "summary_zh": a["title"]}
                  for i, a in enumerate(articles)]

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

    print(f"Scoring top articles with Gemini...")
    top = score_with_gemini(unique)

    # Add unique IDs and clean up
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i, a in enumerate(top):
        a["id"] = f"{today}-{make_id(a['url'], a['published_at'])}"
        a.pop("snippet", None)

    OUTPUT_FILE.write_text(json.dumps(top, ensure_ascii=False, indent=2))
    print(f"Wrote {len(top)} articles to {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
