"""
generate_site.py
Copies JSON data files to docs/data/ and renders docs/index.html
using the Jinja2 template in templates/.
The HTML loads data at runtime via fetch(), keeping index.html small and stable.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ── Config ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
DATA_DIR     = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
DOCS_DIR     = ROOT / "docs"
OUTPUT_FILE  = DOCS_DIR / "index.html"

# JSON files to publish into docs/data/
DATA_FILES = ["news.json", "models.json", "mcp.json", "skills.json", "ides.json", "tools.json"]


def load_json(filename: str) -> list | dict:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Could not load {filename}: {e}")
        return []


def copy_data_files():
    """Copy data/*.json → docs/data/*.json for fetch() access."""
    dest_dir = DOCS_DIR / "data"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for filename in DATA_FILES:
        src = DATA_DIR / filename
        if src.exists():
            shutil.copy2(src, dest_dir / filename)
            print(f"  Copied {filename} → docs/data/")
        else:
            print(f"  [WARN] {filename} not found, skipping")


def main():
    print("=== generate_site.py ===")

    # ── Copy JSON files to docs/data/ ────────────────────────────────────────
    copy_data_files()

    # ── Load stats only (for template rendering) ─────────────────────────────
    news   = load_json("news.json")
    models = load_json("models.json")
    mcp    = load_json("mcp.json")
    skills = load_json("skills.json")
    ides   = load_json("ides.json")
    tools  = load_json("tools.json")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Render template ───────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("index.html.j2")
    html = template.render(
        generated_at=generated_at,
    )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"  News: {len(news)} | Models: {len(models)} | MCP: {len(mcp)}")
    print(f"  Skills: {len(skills)} | IDEs: {len(ides)} | Tools: {len(tools)}")

if __name__ == "__main__":
    main()
