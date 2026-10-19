#!/usr/bin/env python3
"""Build the Double Daily site: regenerates index.html, about.html, and every
post page from config.json + posts/*.json + templates/. Pure stdlib."""
import html, json, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def esc(s): return html.escape(str(s), quote=True)

def paragraphs(text):
    parts = [p.strip() for p in str(text).split("\n\n") if p.strip()]
    return "\n".join(f"  <p>{esc(p)}</p>" for p in parts)

def date_long(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %-d, %Y")

def load_posts():
    posts = []
    for f in sorted((ROOT / "posts").glob("*.json")):
        p = json.loads(f.read_text())
        p["_file"] = f.name
        posts.append(p)
    # newest first; same day: PM before AM
    posts.sort(key=lambda p: (p["date"], 1 if p["slot"].upper() == "PM" else 0), reverse=True)
    return posts

def fill(tpl, mapping):
    out = tpl
    for k, v in mapping.items():
        out = out.replace(f"%%{k}%%", v)
    return out

def main():
    cfg = json.loads((ROOT / "config.json").read_text())
    page_tpl = (ROOT / "templates" / "page.html").read_text()
    post_tpl = (ROOT / "templates" / "post.html").read_text()
    card_tpl = (ROOT / "templates" / "card.html").read_text()
    posts = load_posts()

    def shell(content, page_title, root_prefix, meta_desc):
        return fill(page_tpl, {
            "PAGE_TITLE": esc(page_title), "SITE_TITLE": esc(cfg["site_title"]),
            "TAGLINE": esc(cfg["tagline"]), "CHANNEL_URL": esc(cfg["channel_url"]),
            "CHANNEL_NAME": esc(cfg["channel_name"]), "ROOT": root_prefix,
            "META_DESC": esc(meta_desc), "CONTENT": content,
        })

    # --- post pages ---
    for p in posts:
        sources = "\n".join(
            f'      <li><a href="{esc(s["url"])}">{esc(s["name"])}</a></li>'
            if s.get("url") else f"      <li>{esc(s['name'])}</li>"
            for s in p.get("sources", []))
        content = fill(post_tpl, {
            "SLOT": esc(p["slot"].upper()), "SLOT_CLASS": p["slot"].lower(),
            "TITLE": esc(p["title"]), "DATE_LONG": esc(date_long(p["date"])),
            "YOUTUBE_ID": esc(p["youtube_id"]), "BODY": paragraphs(p["body"]),
            "COMPANY_NAME": esc(p["company"]["name"]),
            "COMPANY_TEXT": paragraphs(p["company"]["text"]),
            "SOURCES": sources, "ROOT": "../",
        })
        out = ROOT / "posts" / f'{p["slug"]}.html'
        out.write_text(shell(content, p["title"], "../", p["summary"]))

    # --- home ---
    def card(p):
        return fill(card_tpl, {
            "SLOT": esc(p["slot"].upper()), "SLOT_CLASS": p["slot"].lower(),
            "SLUG": esc(p["slug"]), "TITLE": esc(p["title"]),
            "DATE_LONG": esc(date_long(p["date"])), "SUMMARY": esc(p["summary"]),
        })
    if posts:
        latest_date = posts[0]["date"]
        today = [p for p in posts if p["date"] == latest_date]
        rest = [p for p in posts if p["date"] != latest_date]
        home = ['<h2 class="section">Latest &mdash; ' + esc(date_long(latest_date)) + "</h2>"]
        home += [card(p) for p in today]
        if rest:
            home.append('<h2 class="section">Archive</h2>')
            home += [card(p) for p in rest]
        home_html = "\n".join(home)
    else:
        home_html = ('<h2 class="section">Latest</h2>\n'
                     '<p class="empty">The first documentary posts here today &mdash; '
                     '9:00 AM and 4:00 PM (America/Chicago). Watch on the '
                     f'<a href="{esc(cfg["channel_url"])}">{esc(cfg["channel_name"])}</a> YouTube channel.</p>')
    (ROOT / "index.html").write_text(
        shell(home_html, "Home", "", cfg["tagline"]))

    # --- about ---
    about = """<article class="post">
  <h2>About</h2>
  <p>Twice a day &mdash; 9:00 AM and 4:00 PM, America/Chicago &mdash; this blog carries a short American
  documentary from the %%CHANNEL_NAME%% YouTube channel: where a story started, where it stands today,
  and what comes next. Facts only. Every fact is checked, sourced, and credited on the post itself,
  and every illustration is original. No heat, no hype &mdash; just the story, told straight.</p>
</article>""".replace("%%CHANNEL_NAME%%", esc(cfg["channel_name"]))
    (ROOT / "about.html").write_text(
        shell(about, "About", "", "About " + cfg["site_title"]))
    print(f"Built {len(posts)} post(s): index.html, about.html, posts/*.html")

if __name__ == "__main__":
    sys.exit(main())
