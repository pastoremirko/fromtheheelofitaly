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
    "people": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/><circle cx="17" cy="9.5" r="2.6"/><path d="M15.5 14.3c.5-.2 1-.3 1.5-.3 2.8 0 4.5 2.1 4.5 5"/></svg>',
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
    links = [(f"/{a['slug']}/", a["short"], a["slug"]) for a in SITE["areas"]]
    items = "".join(
        f'<a href="{u}"{" class=active" if k == active else ""}>{esc(t)}</a>' for u, t, k in links)
    items += f'<a href="/about/"{" class=active" if active == "about" else ""}>About</a>'
    items += '<a class="btn-sub" href="/support/">Support</a>'
    return items


def layout(title, content, description=None, active="", image=None, path="/"):
    full_title = f"{SITE['title']} · Updates from Pieno Vangelo" if title == SITE["title"] else f"{title} · {SITE['title']}"
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
<meta name="theme-color" content="#f6f6f6">
{'<meta name="robots" content="noindex, nofollow">' if SITE.get("draft_mode") else ''}
<link rel="icon" href="/img/pv-glifo.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/manrope-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'])}" href="/feed.xml">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><img class="pv-logo" src="/img/pv-glifo.svg" alt="Chiesa Pienovangelo"><span class="sep"></span><span class="upd">Updates</span></a>
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
        <a class="foot-brand" href="https://pienovangelo.it" rel="noopener"><img src="/img/pv-glifo.svg" alt="Chiesa Pienovangelo"></a>
        <p class="brandline">From the Heel of Italy<br><em>to the ends of the earth</em></p>
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
          {contact}{socials}
          <li><a href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a></li>
          <li><a href="/feed.xml">RSS feed</a></li>
        </ul>
      </div>
    </div>
    <p class="small">© {year} {esc(SITE['church'])} · Modugno (BA), Italy · <a href="/privacy/">Privacy</a></p>
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
    <h3>{esc(p['title'])}</h3>
    <p>{esc(p['excerpt'])}</p>
    <span class="meta">{fmt_date(p['date'])} · Read more →</span>
  </div>
</a>"""


def cards_grid(posts, empty="The first update is on its way.", cls=""):
    if not posts:
        return f'<div class="empty">{esc(empty)}</div>'
    return f'<div class="grid {cls}">' + "".join(card(p) for p in posts) + "</div>"


def window_bg(a):
    if a.get("image"):
        return f'<div class="bg"><img src="{esc(a["image"])}" alt="" loading="lazy"></div>'
    return f'<div class="bg ph" {style_c(a)}>{ICONS[a["icon"]]}</div>'


def area_window(a, n):
    label = f"{n} update{'s' if n != 1 else ''}" if n else "Coming soon"
    if a.get("image"):
        img = f'<div class="media"><img src="{esc(a["image"])}" alt="" loading="lazy"></div>'
    else:
        img = f'<div class="media ph" {style_c(a)}>{ICONS[a["icon"]]}</div>'
    return f"""<a class="area-card" href="/{a['slug']}/" {style_c(a)}>
  {img}
  <div class="body">
    <span class="tag">{label}</span>
    <h3>{esc(a['name'])}</h3>
    <p>{esc(a['intro'])}</p>
    <span class="go">Read the updates</span>
  </div>
</a>"""


def subscribe_band():
    return f"""<section class="subscribe" id="subscribe"><div class="wrap"><div class="box">
  <div>
    <h2 class="display">Walk <em>with us</em></h2>
    <p>A short update every few weeks: one story, one photo and a link to read more. No spam, unsubscribe anytime.</p>
  </div>
  <div class="actions">
    <a class="btn btn-primary" href="{SITE['subscribe_url']}">Subscribe</a>
    <a class="btn btn-light" href="/support/">Support the work</a>
  </div>
</div></div></section>"""


def chips(active=""):
    items = [("/updates/", "All", "")] + [(f"/{a['slug']}/", a["short"], a["slug"]) for a in SITE["areas"]]
    return '<nav class="chips">' + "".join(
        f'<a href="{u}"{" class=on" if k == active else ""}>{esc(t)}</a>' for u, t, k in items) + "</nav>"


def page_home(posts):
    counts = {a["slug"]: sum(1 for p in posts if p["area"]["slug"] == a["slug"]) for a in SITE["areas"]}
    windows = "".join(area_window(a, counts[a["slug"]]) for a in SITE["areas"])
    windows += f"""<a class="area-card cta" href="/support/">
  <div class="body">
    <span class="tag">Partner with us</span>
    <h3>Support the work</h3>
    <p>Pray with us, give, or come and visit. Every area of this ministry is carried by friends like you.</p>
    <span class="go">How to help</span>
  </div>
</a>"""
    latest = ""
    if posts:
        latest = featured(posts[0])
        if len(posts) > 1:
            latest += cards_grid(posts[1:4], cls="top")
    else:
        latest = '<div class="empty">The first update is on its way.</div>'
    content = f"""<div class="intro"><div class="wrap">
  <h1 class="display">From the Heel of Italy</h1>
  <div class="sub">
    <p class="lead">&hellip; <em>to the ends of the earth</em>. Updates from the Pieno Vangelo ministry and the Ronchi family.</p>
    <div class="actions">
      <a class="btn btn-primary" href="{SITE['subscribe_url']}">Get the newsletter</a>
      <a class="btn btn-outline" href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a>
    </div>
  </div>
</div></div>
<section><div class="wrap">
  <div class="section-head">
    <h2 class="display">Latest updates</h2>
    <a class="link" href="/updates/">All updates →</a>
  </div>
  {latest}
</div></section>
<section><div class="wrap">
  <div class="section-head">
    <h2 class="display">Updates by area</h2>
  </div>
  <div class="areas">{windows}</div>
</div></section>
{subscribe_band()}"""
    return layout(SITE["title"], content, active="home")


def page_updates(posts):
    content = f"""<header class="page-head"><div class="wrap">
  <p class="eyebrow">News &amp; stories</p>
  <h1 class="display">All <em>updates</em></h1>
  {chips("")}
</div></header>
<section><div class="wrap">{cards_grid(posts)}</div></section>
{subscribe_band()}"""
    return layout("Updates", content, active="updates", path="/updates/")


def page_area(a, posts):
    mine = [p for p in posts if p["area"]["slug"] == a["slug"]]
    content = f"""<div class="area-hero"><div class="wrap">
  <div class="window{' has-img' if a.get('image') else ''}" {style_c(a)}>
    {window_bg(a)}
    <div class="inner">
      <span class="count">{(str(len(mine)) + ' update' + ('s' if len(mine) != 1 else '')) if mine else 'Coming soon'}</span>
      <h1>{esc(a['name'])}</h1>
      <p>{esc(a['intro'])}</p>
    </div>
  </div>
  {chips(a['slug'])}
</div></div>
{area_about(a)}
<section><div class="wrap">
  {'<div class="section-head"><h2 class="display">Latest updates</h2></div>' if (ROOT / "content" / "areas" / (a["slug"] + ".md")).exists() else ''}
  {cards_grid(mine, "The first update from this area is on its way.")}
</div></section>
{subscribe_band()}"""
    return layout(a["name"], content, description=a["intro"], active=a["slug"], path=f"/{a['slug']}/")


def area_about(a):
    """Optional presentation (text + video) from content/areas/<slug>.md"""
    path = ROOT / "content" / "areas" / f"{a['slug']}.md"
    if not path.exists():
        return ""
    meta, body = parse_md(path)
    video = video_embed(meta.get("video", ""))
    return f"""<section class="area-about"><div class="wrap"><div class="about-grid{' has-video' if video else ''}">
  {f'<div class="about-video">{video}</div>' if video else ''}
  <div class="about-text prose">
    <h2>{esc(meta.get('title', 'About'))}</h2>
    {render_body(body)}
  </div>
</div></div></section>"""


def page_post(p, posts):
    a = p["area"]
    eyebrow = (f'<a class="eyebrow" href="/{a["slug"]}/">{esc(a["name"])}</a>' if a["slug"]
               else f'<p class="eyebrow">{esc(a["name"])}</p>')
    more = [q for q in posts if q is not p and (q["area"]["slug"] == a["slug"] or not a["slug"])][:3]
    more_html = ""
    if more:
        title = f"More from {esc(a['name'])}" if a["slug"] else "More updates"
        more_html = f"""<section><div class="wrap">
  <div class="section-head"><h2 class="display">{title}</h2></div>
  {cards_grid(more)}
</div></section>"""
    back = (f'<a href="/{a["slug"]}/">← All {esc(a["name"])} updates</a>' if a["slug"]
            else '<a href="/updates/">← All updates</a>')
    cover = f'<div class="article-cover">{media(p)}</div>' if p["cover"] else ""
    content = f"""<article>
  <header class="article-head"><div class="narrow">
    {eyebrow}
    <h1 class="display">{esc(p['title'])}</h1>
    <div class="meta">{fmt_date(p['date'])} · {esc(SITE['author'])}</div>
  </div></header>
  {cover}
  <div class="narrow page-body"><div class="prose-card prose">{p['html']}
    <div class="article-foot">{back}<a href="{SITE['subscribe_url']}">Get updates by email →</a></div>
  </div></div>
</article>
{more_html}
{subscribe_band()}"""
    return layout(p["title"], content, description=p["excerpt"], active=a["slug"],
                  image=p["cover"] or None, path=p["url"])


def page_simple(slug, meta, body):
    content = f"""<header class="page-head"><div class="narrow">
  <h1 class="display">{esc(meta.get('title', slug))}</h1>
  {f"<p>{esc(meta['intro'])}</p>" if meta.get('intro') else ""}
</div></header>
<div class="narrow page-body"><div class="prose-card prose">{('<div class="about-map">' + (ROOT / "static" / "img" / "map-sketch.svg").read_text(encoding="utf-8") + '</div>') if slug == 'about' else ''}{render_body(body)}</div></div>
{subscribe_band() if slug != 'privacy' else ''}"""
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
  <h1 class="display">Page <em>not found</em></h1><p>The page you are looking for is not here. <a href="/">Go back home</a>.</p>
</div></header>"""))
    print(f"Built {len(posts)} posts into {OUT}")


if __name__ == "__main__":
    main()
