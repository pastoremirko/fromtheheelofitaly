#!/usr/bin/env python3
"""Build the From the Heel of Italy static site.

Usage:  python3 build.py
Reads site.json, content/posts/*.md, content/pages/*.md and static/,
writes the finished site to public/.
"""
import html
import json
import re
import shutil
from datetime import date, datetime
from email.utils import format_datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "public"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
AREAS = {a["slug"]: a for a in SITE["areas"]}
GENERAL = {"slug": "", "name": "News", "short": "News", "color": "#e74759", "icon": "church"}

ICONS = {
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5h13V10"/><path d="M12 17.5s-3-1.8-3-3.8a1.6 1.6 0 0 1 3-.8 1.6 1.6 0 0 1 3 .8c0 2-3 3.8-3 3.8z"/></svg>',
    "church": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v5M10 4h4"/><path d="M6 21V11l6-4 6 4v10"/><path d="M3 21h18"/><path d="M10 21v-4a2 2 0 0 1 4 0v4"/></svg>',
    "tent": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4 3 20h18L12 4z"/><path d="M12 4v16"/><path d="m9 20 3-6 3 6"/><path d="M2 20h20"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
    "seed": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21v-9"/><path d="M12 12c0-4 3-7 8-7 0 5-3 7-8 7z"/><path d="M12 14c0-3-2.5-5.5-7-5.5 0 4 2.5 5.5 7 5.5z"/><path d="M7 21h10"/></svg>',
    "mark": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="51" r="7" fill="currentColor" stroke="none"/><path d="M22 43C30 28 38 20 52 13" stroke-dasharray="0.1 9"/><path d="M42 9.5 55 11l-4.5 12"/></svg>',
}

esc = html.escape


# ---------- content loading ----------

def parse_md(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    return meta, body


def youtube_id(url):
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def video_embed(url):
    vid = youtube_id(url)
    if vid:
        src = f"https://www.youtube-nocookie.com/embed/{vid}"
    else:
        m = re.search(r"vimeo\.com/(\d+)", url or "")
        if not m:
            return ""
        src = f"https://player.vimeo.com/video/{m.group(1)}"
    return (f'<div class="video"><iframe src="{src}" title="Video" loading="lazy" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            'allowfullscreen></iframe></div>')


def render_body(body):
    # A line containing only a YouTube/Vimeo link becomes an embedded video.
    def repl(m):
        emb = video_embed(m.group(1))
        return f"\n{emb}\n" if emb else m.group(0)
    body = re.sub(r"^\s*(https?://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)\S*)\s*$", repl, body, flags=re.M)
    return markdown.markdown(body, extensions=["extra", "smarty"])


def load_posts():
    posts = []
    for p in sorted((ROOT / "content" / "posts").glob("*.md")):
        meta, body = parse_md(p)
        if meta.get("draft", "").lower() in ("true", "yes"):
            continue
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
        d = datetime.strptime(meta.get("date", "2026-01-01"), "%Y-%m-%d").date()
        area = AREAS.get(meta.get("area", ""), GENERAL)
        html_body = render_body(body)
        if meta.get("video"):
            html_body += video_embed(meta["video"])
        excerpt = meta.get("excerpt") or re.sub(r"<[^>]+>", "", html_body)[:200].rsplit(" ", 1)[0] + "…"
        posts.append({
            "title": meta.get("title", slug), "slug": slug, "date": d, "area": area,
            "cover": meta.get("cover", ""), "cover_alt": meta.get("cover_alt", meta.get("title", "")),
            "excerpt": excerpt, "html": html_body, "url": f"/updates/{slug}/",
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


# ---------- templates ----------

def fmt_date(d):
    return d.strftime("%-d %B %Y")


def topics(active=""):
    items = [("/", "All updates", "home")] + [(f"/{a['slug']}/", a["short"], a["slug"]) for a in SITE["areas"]]
    return "".join(f'<a href="{u}"{" class=on" if k == active else ""}>{esc(t)}</a>' for u, t, k in items)


def masthead(active="", compact=False):
    today = date.today().strftime("%A %-d %B %Y")
    title_tag = "div" if compact else "h1"
    return f"""<header class="mast{' compact' if compact else ''}">
  <div class="wrap">
    <div class="mast-top">
      <span>{today}</span>
      <span>News from the Pieno Vangelo ministry · <a href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a></span>
    </div>
    <div class="mast-main">
      <div>
        <{title_tag} class="mast-title"><a href="/">Updates</a></{title_tag}>
        <p class="mast-sub"><strong>From the heel of Italy to the nations.</strong> News from the Pieno Vangelo ministry and the Ronchi family.</p>
      </div>
      <a class="mast-logo" href="https://pienovangelo.it" rel="noopener" aria-label="Pieno Vangelo"><img src="/img/pv-logo.svg" alt="Pieno Vangelo"></a>
    </div>
    <nav class="topics">
      <div class="topics-list">{topics(active)}</div>
      <a class="sub-link" href="{SITE['subscribe_url']}">Subscribe by email</a>
    </nav>
  </div>
</header>"""


def layout(title, content, description=None, active="", image=None, path="/", compact=True):
    full_title = SITE["site_name"] if title == SITE["title"] else f"{title} · {SITE['site_name']}"
    desc = esc(description or SITE["description"])
    url = SITE["base_url"].rstrip("/") + path
    og_img = f'<meta property="og:image" content="{SITE["base_url"].rstrip("/")}{image}">' if image else ""
    year = date.today().year
    noindex = '<meta name="robots" content="noindex, nofollow">' if SITE.get("draft_mode") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
{noindex}
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
{og_img}
<meta name="theme-color" content="#f6f6f6">
<link rel="icon" href="/img/pv-mark.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/manrope-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['site_name'])}" href="/feed.xml">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/blog.css">
</head>
<body>
{masthead(active, compact)}
<main>
{content}
</main>
<footer class="foot">
  <div class="wrap">
    <img src="/img/pv-logo.svg" alt="Pieno Vangelo" class="foot-logo">
    <p>{esc(SITE['church'])} · Modugno (BA), Italy · <a href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a></p>
    <p class="foot-links"><a href="/about/">About these updates</a> · <a href="/support/">Support</a> · <a href="{SITE['subscribe_url']}">Subscribe</a> · <a href="/feed.xml">RSS</a> · <a href="/privacy/">Privacy</a> · © {year}</p>
  </div>
</footer>
</body>
</html>
"""


def style_c(area):
    return f'style="--c:{area["color"]}"'


def media(post, extra=""):
    a = post["area"]
    if post["cover"]:
        return f'<div class="media {extra}"><img src="{esc(post["cover"])}" alt="{esc(post["cover_alt"])}" loading="lazy"></div>'
    return f'<div class="media ph {extra}" {style_c(a)}>{ICONS[a["icon"]]}</div>'


def tag_html(a):
    return f'<span class="tag">{esc(a["name"])}</span>'


def card(p):
    return f"""<a class="card" href="{p['url']}">
  {media(p)}
  <div class="body">
    {tag_html(p['area'])}
    <h3>{esc(p['title'])}</h3>
    <p>{esc(p['excerpt'])}</p>
    <span class="meta">{fmt_date(p['date'])}</span>
  </div>
</a>"""


def featured(p):
    return f"""<a class="featured" href="{p['url']}">
  {media(p)}
  <div class="body">
    {tag_html(p['area'])}
    <h2>{esc(p['title'])}</h2>
    <p>{esc(p['excerpt'])}</p>
    <span class="meta">{fmt_date(p['date'])} · Read more →</span>
  </div>
</a>"""


def cards_grid(posts, empty="The first update is on its way.", cls=""):
    if not posts:
        return f'<div class="empty">{esc(empty)}</div>'
    return f'<div class="grid {cls}">' + "".join(card(p) for p in posts) + "</div>"


def map_strip():
    svg = (ROOT / "static" / "img" / "map-sketch.svg").read_text(encoding="utf-8")
    return f"""<section class="strip"><div class="wrap"><div class="strip-box">
  <div class="strip-map">{svg}</div>
  <div class="strip-text">
    <p class="eyebrow">Why these updates</p>
    <h2>From Bari, in every direction</h2>
    <p>Our local church in Modugno, near Bari, is reaching out across Puglia and Basilicata and sending people overseas. Here we share what God is doing, one story at a time.</p>
    <a class="text-link" href="/about/">About us →</a>
  </div>
</div></div></section>"""


def subscribe_line():
    return f"""<section class="sub-line" id="subscribe"><div class="wrap"><div class="sub-box">
  <p><strong>Get the updates by email.</strong> A short note every few weeks, one story at a time. Unsubscribe anytime.</p>
  <a class="btn btn-primary" href="{SITE['subscribe_url']}">Subscribe</a>
</div></div></section>"""


def page_home(posts):
    if posts:
        latest = featured(posts[0]) + (cards_grid(posts[1:7], cls="top") if len(posts) > 1 else "")
    else:
        latest = '<div class="empty">The first update is on its way.</div>'
    content = f"""<section class="feed"><div class="wrap">{latest}</div></section>
{map_strip()}
{subscribe_line()}"""
    return layout(SITE["title"], content, active="home", compact=False)


def page_updates(posts):
    content = f"""<section class="feed"><div class="wrap">{cards_grid(posts)}</div></section>
{subscribe_line()}"""
    return layout("All updates", content, active="home", path="/updates/")


def page_area(a, posts):
    mine = [p for p in posts if p["area"]["slug"] == a["slug"]]
    img = f'<img src="{esc(a["image"])}" alt="" class="area-img">' if a.get("image") else ""
    content = f"""<section class="area-head"><div class="wrap"><div class="area-box{' with-img' if img else ''}" {style_c(a)}>
  <div>
    <p class="eyebrow">Updates on</p>
    <h1>{esc(a['name'])}</h1>
    <p>{esc(a['intro'])}</p>
  </div>
  {img}
</div></div></section>
<section class="feed"><div class="wrap">{cards_grid(mine, "The first update from this area is on its way.")}</div></section>
{subscribe_line()}"""
    return layout(a["name"], content, description=a["intro"], active=a["slug"], path=f"/{a['slug']}/")


def page_post(p, posts):
    a = p["area"]
    eyebrow = (f'<a class="eyebrow" href="/{a["slug"]}/">{esc(a["name"])}</a>' if a["slug"]
               else f'<p class="eyebrow">{esc(a["name"])}</p>')
    more = [q for q in posts if q is not p][:3]
    more_html = f"""<section class="feed"><div class="wrap">
  <h2 class="more-title">More updates</h2>
  {cards_grid(more)}
</div></section>""" if more else ""
    cover = f'<div class="article-cover">{media(p)}</div>' if p["cover"] else ""
    content = f"""<article>
  <header class="article-head"><div class="narrow">
    {eyebrow}
    <h1>{esc(p['title'])}</h1>
    <div class="meta">{fmt_date(p['date'])} · {esc(SITE['author'])}</div>
  </div></header>
  {cover}
  <div class="narrow page-body"><div class="prose-card prose">{p['html']}
    <div class="article-foot"><a href="/">← All updates</a><a href="{SITE['subscribe_url']}">Get updates by email →</a></div>
  </div></div>
</article>
{more_html}
{subscribe_line()}"""
    return layout(p["title"], content, description=p["excerpt"], active=a["slug"],
                  image=p["cover"] or None, path=p["url"])


def page_simple(slug, meta, body):
    content = f"""<section class="area-head"><div class="wrap"><div class="area-box plain">
  <div><h1>{esc(meta.get('title', slug))}</h1>
  {f"<p>{esc(meta['intro'])}</p>" if meta.get('intro') else ""}</div>
</div></div></section>
<div class="narrow page-body"><div class="prose-card prose">{render_body(body)}</div></div>
{subscribe_line() if slug != 'privacy' else ''}"""
    return layout(meta.get("title", slug), content, description=meta.get("intro"), active=slug, path=f"/{slug}/")


def feed(posts):
    base = SITE["base_url"].rstrip("/")
    items = ""
    for p in posts[:20]:
        dt = datetime(p["date"].year, p["date"].month, p["date"].day, 9, 0).astimezone()
        img = f'<enclosure url="{base}{esc(p["cover"])}" type="image/jpeg"/>' if p["cover"] else ""
        items += f"""<item><title>{esc(p['title'])}</title><link>{base}{p['url']}</link>
<guid>{base}{p['url']}</guid><pubDate>{format_datetime(dt)}</pubDate>
<category>{esc(p['area']['name'])}</category><description>{esc(p['excerpt'])}</description>{img}</item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{esc(SITE['site_name'])}</title><link>{base}/</link>
<description>{esc(SITE['description'])}</description><language>en</language>
{items}</channel></rss>
"""


# ---------- build ----------

def write(rel, text):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    posts = load_posts()
    write("index.html", page_home(posts))
    write("updates/index.html", page_updates(posts))
    for a in SITE["areas"]:
        write(f"{a['slug']}/index.html", page_area(a, posts))
    for p in posts:
        write(f"updates/{p['slug']}/index.html", page_post(p, posts))
    for pg in sorted((ROOT / "content" / "pages").glob("*.md")):
        meta, body = parse_md(pg)
        write(f"{pg.stem}/index.html", page_simple(pg.stem, meta, body))
    write("feed.xml", feed(posts))
    write("404.html", layout("Page not found", """<section class="area-head"><div class="wrap"><div class="area-box plain"><div>
  <h1>Page not found</h1><p>The page you are looking for is not here. <a href="/">Back to all updates</a>.</p>
</div></div></div></section>"""))
    print(f"Built {len(posts)} posts into {OUT}")


if __name__ == "__main__":
    main()
