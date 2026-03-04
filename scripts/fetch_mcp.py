"""
fetch_mcp.py
Fetches MCP server list from the awesome-mcp-servers GitHub repo,
parses the Markdown tables, and writes data/mcp.json.
"""

import json
import re
import sys
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ── Config ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_FILE = ROOT / "data" / "mcp.json"

# Primary source: awesome-mcp-servers README
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_readme() -> str | None:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"User-Agent": "AI-Droplet/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.get(GITHUB_RAW_URL, headers=headers, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] Could not fetch README: {e}", file=sys.stderr)
        return None


def parse_markdown_tables(content: str) -> list[dict]:
    """
    Parse MCP entries from the awesome-mcp-servers README.
    Format: - [name](url) 🐍 ☁️ - Description text.
    Sections are headed by ### Category Name
    """
    entries = []
    seen_names = set()

    current_category = "Other"
    lines = content.splitlines()

    # Match ### section headings (only after "Server Implementations")
    heading_re = re.compile(r"^###\s+(?:[^\w]*\s*)?(.+)$")
    # Match list entries: - [text](url) ... - description
    # The name link may be followed by emoji/flag characters, then " - description"
    entry_re = re.compile(
        r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s*(.*?)$"
    )

    in_server_section = False

    for line in lines:
        # Detect entry into "Server Implementations" section
        if "## Server Implementations" in line:
            in_server_section = True
            continue
        if in_server_section and line.startswith("## ") and "Server Implementations" not in line:
            in_server_section = False

        if not in_server_section:
            continue

        # Update category from ### headings
        m = heading_re.match(line)
        if m:
            raw = m.group(1)
            # Pattern: ### 🛠️ <a name="developer-tools"></a>Developer Tools
            # Extract the text that comes after the last > (closing anchor tag)
            anchor_match = re.search(r"</a>\s*(.+)$", raw)
            if anchor_match:
                heading = anchor_match.group(1).strip()
            else:
                # No anchor tag - strip HTML tags and leading emoji with regex
                heading = re.sub(r"<[^>]+>", "", raw)
                # Remove leading emoji/symbols using Unicode ranges
                heading = re.sub(r"^[^\w]+", "", heading).strip()
            if heading and len(heading) < 80:
                current_category = heading
            continue

        # Match entry lines
        m = entry_re.match(line)
        if not m:
            continue

        raw_name = m.group(1).strip()
        url = m.group(2).strip()
        rest = m.group(3).strip()

        # Extract description: everything after the first " - " in rest,
        # stripping leading emoji characters
        desc = ""
        dash_pos = rest.find(" - ")
        if dash_pos >= 0:
            desc = rest[dash_pos + 3:].strip()
        elif rest and not rest[0].isalpha():
            # rest starts with emoji flags, try stripping them
            clean = re.sub(r"^[\U00010000-\U0010ffff\s🎖️🐍📇🏎️🦀#️⃣☕🌊💎☁️🏠📟🍎🪟🐧]+", "", rest).strip()
            if clean.startswith("- "):
                desc = clean[2:].strip()
            else:
                desc = clean

        # Clean markdown from description
        desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)
        desc = desc.strip()[:200]

        # Use the last part of the repo path as display name (e.g. "1mcp/agent" → "agent")
        display_name = raw_name.split("/")[-1] if "/" in raw_name else raw_name
        # If the display name is generic, use full name
        if len(display_name) < 3:
            display_name = raw_name

        if display_name and display_name not in seen_names:
            seen_names.add(display_name)
            entries.append({
                "name": display_name,
                "full_name": raw_name,
                "category": current_category,
                "description": desc if desc else "",
                "url": url,
            })

    return entries


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== fetch_mcp.py ===")

    content = fetch_readme()
    if not content:
        print("[WARN] No content fetched. Keeping existing mcp.json.")
        return

    print(f"README fetched ({len(content):,} chars)")

    entries = parse_markdown_tables(content)
    print(f"Parsed {len(entries)} MCP entries")

    if not entries:
        print("[WARN] No entries parsed. Check README format.")
        return

    # Sort by category then name
    entries.sort(key=lambda x: (x["category"], x["name"].lower()))

    OUTPUT_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(entries)} MCP entries to {OUTPUT_FILE.relative_to(ROOT)}")

    # Print category breakdown
    from collections import Counter
    cats = Counter(e["category"] for e in entries)
    for cat, count in cats.most_common(10):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
