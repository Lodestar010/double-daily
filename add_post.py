#!/usr/bin/env python3
"""Add one post to the site.

Usage:  python3 add_post.py path/to/post-data.json

The data file is JSON with fields:
  title      (string)  video/post title
  youtube_id (string)  YouTube video ID, e.g. "dQw4w9WgXcQ"
  slot       (string)  "AM" or "PM"
  date       (string)  "YYYY-MM-DD"
  summary    (string)  one-line summary for the home page
  body       (string)  the write-up; blank line separates paragraphs
  company    (object)  {"name": "...", "text": "..."} — the company segment
  sources    (list)    [{"name": "...", "url": "https://..."}, ...]

Writes posts/<date>-<slot>-<slug>.json, rebuilds the site, and prints the
post URL path. Commit and push afterwards to publish.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ["title", "youtube_id", "slot", "date", "summary", "body", "company", "sources"]

def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60].rstrip("-")

def main():
    if len(sys.argv) != 2:
        print(__doc__); return 1
    data = json.loads(Path(sys.argv[1]).read_text())
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        print("Missing fields:", ", ".join(missing)); return 1
    if data["slot"].upper() not in ("AM", "PM"):
        print('slot must be "AM" or "PM"'); return 1
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["date"]):
        print('date must be "YYYY-MM-DD"'); return 1
    if "name" not in data["company"] or "text" not in data["company"]:
        print('company needs "name" and "text"'); return 1
    slug = f'{data["date"]}-{data["slot"].lower()}-{slugify(data["title"])}'
    data["slug"] = slug
    out = ROOT / "posts" / f"{slug}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)
    print(f"Post page: posts/{slug}.html")
    return 0

if __name__ == "__main__":
    sys.exit(main())
