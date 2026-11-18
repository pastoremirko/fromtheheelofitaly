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
GENERAL = {"slug": "", "name": "News", "short": "News", "color": "#1F4E79", "icon": "mark"}

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


def nav(active=""):
    links = [("/", "Home", "home"), ("/updates/", "Updates", "updates")]
    links += [(f"/{a['slug']}/", a["short"], a["slug"]) for a in SITE["areas"]]
    links += [("/support/", "Support", "support")]
    items = "".join(
        f'<a href="{u}"{" class=active" if k == active else ""}>{esc(t)}</a>' for u, t, k in links)
    items += f'<a class="btn-sub" href="{SITE["subscribe_url"]}">Subscribe</a>'
    return items


def layout(title, content, description=None, active="", image=None, path="/"):
    full_title = SITE["title"] if title == SITE["title"] else f"{title} · {SITE['title']}"
    desc = esc(description or SITE["description"])
    url = SITE["base_url"].rstrip("/") + path
    og_img = f'<meta property="og:image" content="{SITE["base_url"].rstrip("/")}{image}">' if image else ""
    year = date.today().year
    area_links = "".join(f'<li><a href="/{a["slug"]}/">{esc(a["name"])}</a></li>' for a in SITE["areas"])
    socials = "".join(
        f'<li><a href="{SITE[k]}" rel="noopener">{n}</a></li>'
        for k, n in (("youtube", "YouTube"), ("facebook", "Facebook"), ("instagram", "Instagram")) if SITE.get(k))
    contact = f'<li><a href="mailto:{SITE["contact_email"]}">Email us</a></li>' if SITE.get("contact_email") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
{og_img}
<link rel="icon" href="/img/mark.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'])}" href="/feed.xml">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><img src="/img/mark.svg" alt=""><span>{esc(SITE['title'])}</span></a>
    <button class="nav-toggle" aria-label="Menu" onclick="document.querySelector('.nav').classList.toggle('open')">Menu</button>
    <nav class="nav">{nav(active)}</nav>
  </div>
</header>
<main>
{content}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div>
        <h4>{esc(SITE['title'])}</h4>
        <p>{esc(SITE['description'])}</p>
      </div>
      <div>
        <h4>Areas</h4>
        <ul>{area_links}</ul>
      </div>
      <div>
        <h4>Stay in touch</h4>
        <ul>
          <li><a href="{SITE['subscribe_url']}">Subscribe to the newsletter</a></li>
          <li><a href="/support/">Support the work</a></li>
          <li><a href="/about/">About us</a></li>
          {contact}{socials}
          <li><a href="/feed.xml">RSS feed</a></li>
        </ul>
      </div>
    </div>
    <p class="small">© {year} {esc(SITE['church'])} · <a href="/privacy/">Privacy</a></p>
  </div>
</footer>
</body>
</html>
"""


def style_c(area):
    return f'style="--c:{area["color"]}"'


def cover_html(post, cls="cover"):
    if post["cover"]:
        return f'<div class="{cls}"><img src="{esc(post["cover"])}" alt="{esc(post["cover_alt"])}" loading="lazy"></div>'
    return f'<div class="{cls} placeholder" {style_c(post["area"])}><span>{ICONS[post["area"]["icon"]]}</span></div>'


def post_card(p):
    a = p["area"]
    return f"""<a class="post-card" href="{p['url']}" {style_c(a)}>
  {cover_html(p)}
  <div class="body">
    <span class="tag">{esc(a['short'])}</span>
    <h3>{esc(p['title'])}</h3>
    <p>{esc(p['excerpt'])}</p>
    <span class="meta">{fmt_date(p['date'])}</span>
  </div>
</a>"""


def posts_grid(posts, empty="The first update is on its way."):
    if not posts:
        return f'<div class="empty">{esc(empty)}</div>'
    return '<div class="posts-grid">' + "".join(post_card(p) for p in posts) + "</div>"


def area_card(a):
    return f"""<a class="area-card" href="/{a['slug']}/" {style_c(a)}>
  <span class="icon">{ICONS[a['icon']]}</span>
  <h3>{esc(a['name'])}</h3>
  <p>{esc(a['intro'])}</p>
  <span class="more">See updates →</span>
</a>"""


SUBSCRIBE_BAND = f"""<section class="subscribe" id="subscribe">
  <div class="narrow">
    <h2>Walk with us</h2>
    <p>Receive a short update every few weeks: one story, one photo, and a link to read more. No spam, and you can unsubscribe at any time.</p>
    <a class="btn btn-primary" href="{SITE['subscribe_url']}">Subscribe to the newsletter</a>
  </div>
</section>"""

VERSE = """<section class="verse">
  <div class="wrap">
    <blockquote>“You will be my witnesses in Jerusalem, and in all Judea and Samaria, and to the ends of the earth.”</blockquote>
    <cite>Acts 1:8</cite>
  </div>
</section>"""


def page_home(posts):
    areas = "".join(area_card(a) for a in SITE["areas"])
    content = f"""<section class="hero">
  <div class="wrap">
    <p class="eyebrow">Puglia · Southern Italy</p>
    <h1>{esc(SITE['title'])}</h1>
    <p class="tagline">{esc(SITE['tagline'])}</p>
    <p class="lead">{esc(SITE['description'])}</p>
    <a class="btn btn-primary" href="{SITE['subscribe_url']}">Get the newsletter</a>
    <a class="btn btn-ghost" href="/updates/">Read the updates</a>
  </div>
</section>
<section>
  <div class="wrap">
    <div class="section-head">
      <h2>What we are building</h2>
      <p>Five areas of ministry, all growing out of our local church in Modugno, near Bari.</p>
    </div>
    <div class="areas-grid">{areas}</div>
  </div>
</section>
{VERSE}
<section>
  <div class="wrap">
    <div class="section-head">
      <h2>Latest updates</h2>
      <p><a href="/updates/">See all updates →</a></p>
    </div>
    {posts_grid(posts[:6])}
  </div>
</section>
{SUBSCRIBE_BAND}"""
    return layout(SITE["title"], content, active="home")


def page_updates(posts):
    content = f"""<header class="page-head"><div class="wrap">
  <h1>All updates</h1>
  <p>Every story we have shared, newest first.</p>
</div></header>
<section><div class="wrap">{posts_grid(posts)}</div></section>
{SUBSCRIBE_BAND}"""
    return layout("Updates", content, active="updates", path="/updates/")


def page_area(a, posts):
    mine = [p for p in posts if p["area"]["slug"] == a["slug"]]
    content = f"""<header class="page-head area" {style_c(a)}><div class="wrap">
  <span class="icon">{ICONS[a['icon']]}</span>
  <h1>{esc(a['name'])}</h1>
  <p>{esc(a['intro'])}</p>
</div></header>
<section><div class="wrap">{posts_grid(mine, "The first update from this area is on its way.")}</div></section>
{SUBSCRIBE_BAND}"""
    return layout(a["name"], content, description=a["intro"], active=a["slug"], path=f"/{a['slug']}/")


def page_post(p, posts):
    a = p["area"]
    area_link = f'<a class="tag" href="/{a["slug"]}/">{esc(a["name"])}</a>' if a["slug"] else f'<span class="tag">{esc(a["name"])}</span>'
    more = [q for q in posts if q is not p and q["area"]["slug"] == a["slug"]][:3]
    more_html = ""
    if more:
        more_html = f"""<section><div class="wrap">
  <div class="section-head"><h2>More from {esc(a['name'])}</h2></div>
  {posts_grid(more)}
</div></section>"""
    back = f'<a href="/{a["slug"]}/">← All {esc(a["name"])} updates</a>' if a["slug"] else '<a href="/updates/">← All updates</a>'
    cover = f'<div class="article-cover">{cover_html(p)}</div>' if p["cover"] else ""
    content = f"""<article {style_c(a)}>
  <header class="article-head"><div class="narrow">
    {area_link}
    <h1>{esc(p['title'])}</h1>
    <div class="meta">{fmt_date(p['date'])} · {esc(SITE['author'])}</div>
  </div></header>
  {cover}
  <div class="narrow prose">{p['html']}
    <div class="article-foot">{back}<a href="{SITE['subscribe_url']}">Get updates by email →</a></div>
  </div>
</article>
{more_html}
{SUBSCRIBE_BAND}"""
    return layout(p["title"], content, description=p["excerpt"], active=a["slug"],
                  image=p["cover"] or None, path=p["url"])


def page_simple(slug, meta, body):
    content = f"""<header class="page-head"><div class="wrap">
  <h1>{esc(meta.get('title', slug))}</h1>
  {f"<p>{esc(meta['intro'])}</p>" if meta.get('intro') else ""}
</div></header>
<div class="page-body"><div class="narrow prose">{render_body(body)}</div></div>
{SUBSCRIBE_BAND if slug != 'privacy' else ''}"""
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
<title>{esc(SITE['title'])}</title><link>{base}/</link>
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
    write("404.html", layout("Page not found", """<header class="page-head"><div class="wrap">
  <h1>Page not found</h1><p>The page you are looking for is not here. <a href="/">Go back home</a>.</p>
</div></header>"""))
    print(f"Built {len(posts)} posts into {OUT}")


if __name__ == "__main__":
    main()
