"""
generate_site.py
Reads all JSON data files and renders them into docs/index.html
using the Jinja2 template in templates/.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ── Config ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
DATA_DIR     = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_FILE  = ROOT / "docs" / "index.html"


def load_json(filename: str) -> list | dict:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Could not load {filename}: {e}")
        return []


def main():
    print("=== generate_site.py ===")

    # ── Load all data ────────────────────────────────────────────────────────
    news    = load_json("news.json")
    models  = load_json("models.json")
    mcp     = load_json("mcp.json")
    skills  = load_json("skills.json")
    ides    = load_json("ides.json")
    tools   = load_json("tools.json")

    # ── Compute derived values for the template ──────────────────────────────
    tool_categories = {}
    for t in tools:
        cat = t.get("category", "other")
        tool_categories.setdefault(cat, []).append(t)

    mcp_categories = {}
    for m in mcp:
        cat = m.get("category", "Other")
        mcp_categories.setdefault(cat, []).append(m)

    models_open   = [m for m in models if m.get("type") == "open"]
    models_closed = [m for m in models if m.get("type") == "closed"]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Render template ──────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("index.html.j2")
    html = template.render(
        news=news,
        models=models,
        models_open=models_open,
        models_closed=models_closed,
        mcp=mcp,
        mcp_categories=mcp_categories,
        skills=skills,
        ides=ides,
        tools=tools,
        tool_categories=tool_categories,
        generated_at=generated_at,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"  News: {len(news)} | Models: {len(models)} | MCP: {len(mcp)}")
    print(f"  Skills: {len(skills)} | IDEs: {len(ides)} | Tools: {len(tools)}")
    print(f"  Generated at: {generated_at}")


if __name__ == "__main__":
    main()
