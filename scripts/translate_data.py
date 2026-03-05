"""
translate_data.py
Automatically generates Chinese (_zh) translations for all data/*.json files
using the same AI provider configured in .env.

Fields translated per file:
  models.json   → summary_zh
  tools.json    → description_zh
  skills.json   → description_zh
  ides.json     → tagline_zh, ai_features_zh
  mcp.json      → description_zh  (only those without one; skips empties)

Usage:
  python scripts/translate_data.py              # translate all files
  python scripts/translate_data.py --file tools # translate only tools.json
  python scripts/translate_data.py --force      # re-translate even if _zh exists

Environment (same as fetch_news.py):
  AI_PROVIDER   = gemini (default) | openai
  GEMINI_API_KEY or AI_API_KEY + AI_BASE_URL + AI_MODEL
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

# ── Per-file translation specs ───────────────────────────────────────────────
# Each spec: { "src": source_field, "dst": dest_field, "max_zh": char_limit }
FILE_SPECS = {
    "models.json": [
        {"src": "summary",      "dst": "summary_zh",      "max_zh": 60},
    ],
    "tools.json": [
        {"src": "description",  "dst": "description_zh",  "max_zh": 60},
    ],
    "skills.json": [
        {"src": "description",  "dst": "description_zh",  "max_zh": 80},
    ],
    "ides.json": [
        {"src": "tagline",      "dst": "tagline_zh",      "max_zh": 30},
        {"src": "ai_features",  "dst": "ai_features_zh",  "max_zh": 80},
    ],
    "mcp.json": [
        {"src": "description",  "dst": "description_zh",  "max_zh": 60},
    ],
}

BATCH_SIZE = 40   # items per Gemini call (stay well inside token limit)
SLEEP_BETWEEN_BATCHES = 1.0  # seconds — avoid 429s on free tier

TRANSLATE_PROMPT = """\
You are a professional technical translator. Translate each English AI/tech description \
into concise Simplified Chinese. Keep proper nouns (model names, product names, API names) \
in English. Each translation must be ≤{max_zh} characters.

Return ONLY a JSON array of strings in the same order as the input, e.g.:
["翻译1", "翻译2", ...]

Texts to translate:
{texts}
"""

# ── AI helpers (reuse same pattern as fetch_news.py) ─────────────────────────

def _call_gemini(prompt: str, api_key: str) -> list:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def _call_openai_compat(prompt: str, api_key: str, base_url: str, model_name: str) -> list:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else next(
        (v for v in parsed.values() if isinstance(v, list)), []
    )


def translate_batch(texts: list[str], max_zh: int) -> list[str]:
    """Send a batch of English strings to AI, return translated list."""
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    numbered = "\n".join(f'{i+1}. {t}' for i, t in enumerate(texts))
    prompt = TRANSLATE_PROMPT.format(max_zh=max_zh, texts=numbered)

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in .env")
        result = _call_gemini(prompt, api_key)
    else:
        api_key = os.getenv("AI_API_KEY")
        base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("AI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise ValueError("AI_API_KEY not set in .env")
        result = _call_openai_compat(prompt, api_key, base_url, model_name)

    # Normalise: unwrap if AI returned {"translations": [...]}
    if isinstance(result, dict):
        result = next((v for v in result.values() if isinstance(v, list)), [])

    return [str(r) for r in result]


# ── Per-file logic ────────────────────────────────────────────────────────────

def translate_file(filename: str, spec_list: list[dict], force: bool) -> int:
    """Translate one data file. Returns number of fields written."""
    path = ROOT / "data" / filename
    if not path.exists():
        print(f"  [SKIP] {filename} not found")
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print(f"  [SKIP] {filename} is not a JSON array")
        return 0

    total_written = 0

    for spec in spec_list:
        src_field = spec["src"]
        dst_field = spec["dst"]
        max_zh    = spec["max_zh"]

        # Collect indices where translation is needed
        pending_indices = []
        for i, item in enumerate(data):
            src_val = item.get(src_field, "")
            if not src_val:
                continue  # nothing to translate
            if not force and item.get(dst_field):
                continue  # already translated
            pending_indices.append(i)

        if not pending_indices:
            print(f"  {filename}/{src_field}: all {len(data)} entries already have {dst_field}, skipping")
            continue

        print(f"  {filename}/{src_field}: translating {len(pending_indices)} → {dst_field} …", end="", flush=True)

        # Process in batches
        written = 0
        for batch_start in range(0, len(pending_indices), BATCH_SIZE):
            batch_idx = pending_indices[batch_start:batch_start + BATCH_SIZE]
            texts = [data[i][src_field] for i in batch_idx]

            try:
                translations = translate_batch(texts, max_zh)
            except Exception as e:
                print(f"\n  [ERROR] batch {batch_start//BATCH_SIZE + 1}: {e}")
                continue

            # Write translations back
            for j, idx in enumerate(batch_idx):
                if j < len(translations) and translations[j]:
                    data[idx][dst_field] = translations[j]
                    written += 1

            if batch_start + BATCH_SIZE < len(pending_indices):
                time.sleep(SLEEP_BETWEEN_BATCHES)

        print(f" done ({written}/{len(pending_indices)})")
        total_written += written

    if total_written > 0:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Saved {filename} ({total_written} new translations)")

    return total_written


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Auto-translate _zh fields in data/*.json")
    parser.add_argument("--file",  help="Only translate this file (e.g. 'tools' or 'tools.json')")
    parser.add_argument("--force", action="store_true", help="Re-translate even if _zh already exists")
    args = parser.parse_args()

    target = args.file
    if target and not target.endswith(".json"):
        target += ".json"

    specs = {k: v for k, v in FILE_SPECS.items() if not target or k == target}
    if not specs:
        print(f"Unknown file: {args.file}. Choose from: {list(FILE_SPECS)}")
        sys.exit(1)

    print(f"=== translate_data.py (force={args.force}) ===")
    grand_total = 0
    for filename, spec_list in specs.items():
        grand_total += translate_file(filename, spec_list, force=args.force)

    print(f"\nDone. Total translations written: {grand_total}")
    if grand_total > 0:
        print("Next: run `python scripts/generate_site.py` to rebuild docs/index.html")


if __name__ == "__main__":
    main()
