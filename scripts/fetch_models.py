"""
fetch_models.py
Fetches trending open-source models from HuggingFace API,
merges with hand-curated commercial models, and writes data/models.json.
"""

import json
import sys
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ── Config ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_FILE     = ROOT / "data" / "models.json"
CURATED_FILE    = ROOT / "data" / "models_curated.json"
HF_API_LIMIT    = 50   # how many trending models to pull from HuggingFace

# Note: HuggingFace API no longer supports sort=trending via REST.
# Using sort=likes (most liked overall) as a stable high-quality proxy.
HF_API_URL = (
    "https://huggingface.co/api/models"
    "?sort=likes&direction=-1&limit={limit}&pipeline_tag=text-generation"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_hf_trending(limit: int) -> list[dict]:
    """Fetch trending text-generation models from HuggingFace."""
    url = HF_API_URL.format(limit=limit)
    try:
        resp = httpx.get(url, timeout=30, headers={"User-Agent": "AI-Droplet/1.0"})
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        print(f"[ERROR] HuggingFace API failed: {e}", file=sys.stderr)
        return []

    models = []
    for item in raw:
        model_id = item.get("id", "")
        if not model_id:
            continue
        parts = model_id.split("/")
        provider = parts[0] if len(parts) == 2 else "Community"
        name = parts[-1]

        # Skip obvious fine-tune noise (GGUF, merged, etc.)
        noise_keywords = ["gguf", "merged", "finetune", "lora", "quant"]
        if any(k in name.lower() for k in noise_keywords):
            continue

        models.append({
            "name": name,
            "provider": provider,
            "type": "open",
            "modality": ["text"],
            "released_at": item.get("createdAt", "")[:10] if item.get("createdAt") else "",
            "summary": f"Popular open-source model on HuggingFace with {item.get('likes', 0):,} likes.",
            "url": f"https://huggingface.co/{model_id}",
            "huggingface_id": model_id,
            "likes": item.get("likes", 0),
            "downloads": item.get("downloads", 0),
        })

    return models


def load_curated() -> list[dict]:
    """Load the hand-curated commercial models."""
    try:
        return json.loads(CURATED_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not load curated models: {e}", file=sys.stderr)
        return []


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== fetch_models.py ===")

    curated = load_curated()
    print(f"Curated models loaded: {len(curated)}")

    hf_models = fetch_hf_trending(HF_API_LIMIT)
    print(f"HuggingFace top-liked models fetched: {len(hf_models)}")

    # Merge: curated first (pinned at top), then HF trending
    # Deduplicate by huggingface_id to avoid repetition
    curated_ids = {m.get("huggingface_id") for m in curated if m.get("huggingface_id")}
    hf_deduped = [m for m in hf_models if m.get("huggingface_id") not in curated_ids]

    merged = curated + hf_deduped

    # Sort: curated first (no likes), then HF by likes
    closed = [m for m in merged if m.get("type") == "closed"]
    open_source = [m for m in merged if m.get("type") == "open"]
    open_source.sort(key=lambda x: x.get("likes", 0), reverse=True)

    final = closed + open_source

    OUTPUT_FILE.write_text(json.dumps(final, ensure_ascii=False, indent=2))
    print(f"Wrote {len(final)} models to {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"  Closed-source: {len(closed)}, Open-source: {len(open_source)}")


if __name__ == "__main__":
    main()
