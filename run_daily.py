"""
run_daily.py
One-click runner: fetches all data, generates the site, and optionally pushes to GitHub.

Usage:
    python run_daily.py           # fetch + generate only (no git push)
    python run_daily.py --push    # fetch + generate + git commit & push
    python run_daily.py --skip-news --push  # skip slow news fetch, still push
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent

SCRIPTS = [
    ("fetch_news.py",   "📰 Fetching news..."),
    ("fetch_models.py", "🤖 Fetching models..."),
    ("fetch_mcp.py",    "🔧 Fetching MCP servers..."),
    ("generate_site.py","🌐 Generating site..."),
]

def run_script(name: str, label: str) -> bool:
    print(f"\n{label}")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"  [ERROR] {name} failed with exit code {result.returncode}")
        return False
    return True


def git_push(date_str: str):
    print("\n📤 Committing and pushing to GitHub...")
    cmds = [
        ["git", "add", "data/", "docs/"],
        ["git", "commit", "-m", f"data: update {date_str}"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            # "nothing to commit" is exit code 1 for git commit – not a real error
            if cmd[1] == "commit":
                print("  (nothing new to commit)")
            else:
                print(f"  [ERROR] {' '.join(cmd)} failed")
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description="AI Droplet daily update runner")
    parser.add_argument("--push",       action="store_true", help="Git commit and push after generation")
    parser.add_argument("--skip-news",  action="store_true", help="Skip fetch_news.py (saves Gemini API quota)")
    parser.add_argument("--skip-models",action="store_true", help="Skip fetch_models.py")
    parser.add_argument("--skip-mcp",   action="store_true", help="Skip fetch_mcp.py")
    args = parser.parse_args()

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"╔══════════════════════════════════════╗")
    print(f"║  AI Droplet Daily Update  {date_str}  ║")
    print(f"╚══════════════════════════════════════╝")

    skips = {
        "fetch_news.py":   args.skip_news,
        "fetch_models.py": args.skip_models,
        "fetch_mcp.py":    args.skip_mcp,
    }

    failures = []
    for script, label in SCRIPTS:
        if skips.get(script, False):
            print(f"\n⏭  Skipping {script}")
            continue
        if not run_script(script, label):
            failures.append(script)

    if failures:
        print(f"\n⚠  Completed with errors in: {', '.join(failures)}")
    else:
        print(f"\n✅ All steps completed successfully.")

    if args.push:
        git_push(date_str)
    else:
        print("\nℹ  Run with --push to commit and deploy to GitHub Pages.")

    print(f"\nDone. Open docs/index.html in your browser to preview.")


if __name__ == "__main__":
    main()
