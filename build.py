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
BASE_SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
LANGS = ["en", "nl"]
UI = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
# Set per language by set_lang()
LANG, PFX, SITE, AREAS, T = "en", "", BASE_SITE, {}, UI["en"]
GENERAL = {"slug": "", "name": "News", "short": "News", "color": "#e74759", "icon": "church"}


def set_lang(lang):
    """Switch every template to one language. English lives at /, others at /<lang>/."""
    global LANG, PFX, SITE, AREAS, T, GENERAL
    LANG, PFX, T = lang, ("" if lang == "en" else f"/{lang}"), UI[lang]
    SITE = json.loads(json.dumps(BASE_SITE))
    over = ROOT / f"site.{lang}.json"
    if over.exists():
        o = json.loads(over.read_text(encoding="utf-8"))
        by_slug = o.pop("areas", {})
        SITE.update(o)
        for a in SITE["areas"]:
            a.update(by_slug.get(a["slug"], {}))
    SITE["subscribe_url"] = PFX + BASE_SITE["subscribe_url"]
    AREAS = {a["slug"]: a for a in SITE["areas"]}
    GENERAL = {**GENERAL, "name": T["news"], "short": T["news"]}


def u(path):
    """Site-internal link in the current language."""
    return PFX + path


def tr(path):
    """content/<...> file in the current language, falling back to English."""
    if LANG != "en":
        alt = ROOT / "content" / LANG / path.relative_to(ROOT / "content")
        if alt.exists():
            return alt
    return path


FLAGS = {
    "en": '<svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><clipPath id="fl-t"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath><path d="M0,0v30h60v-30z" fill="#012169"/><path d="M0,0L60,30M60,0L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0L60,30M60,0L0,30" clip-path="url(#fl-t)" stroke="#C8102E" stroke-width="4"/><path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/><path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/></svg>',
    "nl": '<svg viewBox="0 0 9 6" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><path fill="#21468B" d="M0 0h9v6H0z"/><path fill="#fff" d="M0 0h9v4H0z"/><path fill="#AE1C28" d="M0 0h9v2H0z"/></svg>',
}


def lang_switch(path):
    out = []
    for lg in LANGS:
        href = ("" if lg == "en" else f"/{lg}") + path
        cur = ' class="on" aria-current="true"' if lg == LANG else ""
        out.append(f'<a href="{href}" hreflang="{lg}" lang="{lg}" title="{UI[lg]["lang_name"]}"{cur}>{FLAGS[lg]}<span>{lg.upper()}</span></a>')
    return '<div class="lang">' + "".join(out) + "</div>"

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
        meta, body = parse_md(tr(p))
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
            "cover_fit": meta.get("cover_fit", "").lower() in ("true", "yes"),
            "gallery": [g.strip() for g in meta.get("gallery", "").split(",") if g.strip()],
            "excerpt": excerpt, "html": html_body, "url": u(f"/updates/{slug}/"), "path": f"/updates/{slug}/",
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


# ---------- templates ----------

def fmt_date(d):
    return f"{d.day} {T['months'][d.month - 1]} {d.year}"


def n_updates(n):
    return T["coming_soon"] if not n else f"{n} {T['update'] if n == 1 else T['updates']}"


def nav(active=""):
    links = [(u("/about/"), T["about"], "about")] + [(u(f"/{a['slug']}/"), a["short"], a["slug"]) for a in SITE["areas"]]
    items = "".join(
        f'<a href="{u}"{" class=active" if k == active else ""}>{esc(t)}</a>' for u, t, k in links)
    items += f'<a class="btn-sub" href="{u("/support/")}">{T["support"]}</a>'
    return items


LIGHTBOX = """<div class="lightbox" hidden><button class="lb-close" aria-label="Close">×</button><button class="lb-prev" aria-label="Previous">‹</button><img alt=""><button class="lb-next" aria-label="Next">›</button></div>
<script>{
  const box = document.querySelector('.lightbox'), big = box.querySelector('img');
  let set = [], i = 0;
  const show = () => { big.src = set[i].currentSrc || set[i].src; big.alt = set[i].alt;
    box.classList.toggle('single', set.length < 2); };
  document.addEventListener('click', e => {
    const im = e.target.closest('.ap-img img, .prose img, .article-cover img');
    if (!im || im.closest('.lightbox')) return;
    const scope = im.closest('article') || document;
    set = [...scope.querySelectorAll('.ap-img img, .prose img, .article-cover img')].filter(x => x.offsetParent);
    i = Math.max(0, set.indexOf(im)); show(); box.hidden = false; document.body.style.overflow = 'hidden';
  });
  const close = () => { box.hidden = true; document.body.style.overflow = ''; };
  box.addEventListener('click', e => { if (e.target === box || e.target.classList.contains('lb-close')) close(); });
  box.querySelector('.lb-prev').onclick = () => { i = (i - 1 + set.length) % set.length; show(); };
  box.querySelector('.lb-next').onclick = () => { i = (i + 1) % set.length; show(); };
  addEventListener('keydown', e => { if (box.hidden) return;
    if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') box.querySelector('.lb-prev').click();
    if (e.key === 'ArrowRight') box.querySelector('.lb-next').click(); });
}</script>
"""


def layout(title, content, description=None, active="", image=None, path="/"):
    full_title = f"{SITE['title']} · {T['title_suffix']}" if title == SITE["title"] else f"{title} · {SITE['title']}"
    desc = esc(description or SITE["description"])
    base = SITE["base_url"].rstrip("/")
    url = base + PFX + path
    alternates = "".join(f'<link rel="alternate" hreflang="{lg}" href="{base}{"" if lg == "en" else "/" + lg}{path}">' for lg in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{base}{path}">'
    og_img = f'<meta property="og:image" content="{SITE["base_url"].rstrip("/")}{image}">' if image else ""
    year = date.today().year
    area_links = "".join(f'<li><a href="{u("/" + a["slug"] + "/")}">{esc(a["name"])}</a></li>' for a in SITE["areas"])
    socials = "".join(
        f'<li><a href="{SITE[k]}" rel="noopener">{n}</a></li>'
        for k, n in (("youtube", "YouTube"), ("facebook", "Facebook"), ("instagram", "Instagram")) if SITE.get(k))
    contact = f'<li><a href="mailto:{SITE["contact_email"]}">{T["email_us"]}</a></li>' if SITE.get("contact_email") else ""
    return f"""<!doctype html>
<html lang="{LANG}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{alternates}
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
{og_img}
<meta name="theme-color" content="#f6f6f6">
{'<meta name="robots" content="noindex, nofollow">' if SITE.get("draft_mode") else ''}
<link rel="icon" href="/img/pv-glifo.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/manrope-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'])}" href="{u('/feed.xml')}">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{u('/')}" aria-label="{esc(SITE['title'])} – home"><img class="pv-logo" src="/img/pv-glifo.svg" alt="Chiesa Pienovangelo"></a>
    {lang_switch(path)}
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
        <p class="brandline">{T['brand_1']}<br><em>{T['brand_2']}</em></p>
        <p>{esc(SITE['description'])}</p>
      </div>
      <div>
        <h4>{T['areas']}</h4>
        <ul>{area_links}</ul>
      </div>
      <div>
        <h4>{T['stay_in_touch']}</h4>
        <ul>
          <li><a href="{SITE['subscribe_url']}">{T['subscribe_newsletter']}</a></li>
          <li><a href="{u('/support/')}">{T['support_the_work']}</a></li>
          {contact}{socials}
          <li><a href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a></li>
          <li><a href="{u('/feed.xml')}">RSS feed</a></li>
        </ul>
      </div>
    </div>
    <p class="small">© {year} {esc(SITE['church'])} · Modugno (BA), {T['italy']} · <a href="{u('/privacy/')}">Privacy</a></p>
  </div>
</footer>
{LIGHTBOX}
</body>
</html>
"""


def style_c(area):
    return f'style="--c:{area["color"]}"'


def media(post, extra=""):
    a = post["area"]
    if post["cover"]:
        fit = ' class="fit"' if post.get("cover_fit") else ""
        return f'<div class="media {extra}"><img{fit} src="{esc(post["cover"])}" alt="{esc(post["cover_alt"])}" loading="lazy"></div>'
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
    <span class="meta">{fmt_date(p['date'])} · {T['read_more']}</span>
  </div>
</a>"""


def cards_grid(posts, empty=None, cls=""):
    empty = empty or T["first_update"]
    if not posts:
        return f'<div class="empty">{esc(empty)}</div>'
    return f'<div class="grid {cls}">' + "".join(card(p) for p in posts) + "</div>"


def video_cover(a):
    """Area video in the hero, in place of the photo: a photo with a play button.
    On the live site a click plays the video in the page; elsewhere (e.g. previews
    that block embedded players) the link opens the video on YouTube."""
    vid = youtube_id(a.get("video", ""))
    if not vid:
        return ""
    poster = (f'<img src="{esc(a["image"])}" alt="" loading="lazy">' if a.get("image")
              else f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy">')
    return (f'<div class="bg bg-video"><a class="yt-facade" href="https://www.youtube.com/watch?v={vid}" '
            f'target="_blank" rel="noopener" data-yt="{vid}" data-title="{esc(a["name"])}" '
            f'aria-label="{esc(T["watch_video"])}: {esc(a["name"])}">{poster}'
            f'<span class="yt-play" aria-hidden="true"></span><span class="yt-label">{esc(T["watch_video"])}</span></a></div>')


VIDEO_SCRIPT = """<script>{
  const live = /(^|\\.)fromtheheelofitaly\\.org$|\\.workers\\.dev$|\\.pages\\.dev$|^localhost$|^127\\.0\\.0\\.1$/.test(location.hostname);
  document.querySelectorAll('.yt-facade').forEach(a => a.addEventListener('click', e => {
    if (!live) return;
    e.preventDefault();
    const f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + a.dataset.yt + '?autoplay=1';
    f.title = a.dataset.title;
    f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    f.allowFullscreen = true;
    a.replaceWith(f);
  }));
}</script>"""


def window_bg(a):
    if a.get("image"):
        return f'<div class="bg"><img src="{esc(a["image"])}" alt="" loading="lazy"></div>'
    return f'<div class="bg ph" {style_c(a)}>{ICONS[a["icon"]]}</div>'


def area_window(a, n):
    label = n_updates(n)
    if a.get("image"):
        img = f'<div class="media"><img src="{esc(a["image"])}" alt="" loading="lazy"></div>'
    else:
        img = f'<div class="media ph" {style_c(a)}>{ICONS[a["icon"]]}</div>'
    return f"""<a class="area-card" href="{u('/' + a['slug'] + '/')}" {style_c(a)}>
  {img}
  <div class="body">
    <span class="tag">{label}</span>
    <h3>{esc(a['name'])}</h3>
    <p>{esc(a['intro'])}</p>
    <span class="go">{T['read_the_updates']}</span>
  </div>
</a>"""


def subscribe_band():
    return f"""<section class="subscribe" id="subscribe"><div class="wrap"><div class="box">
  <div>
    <h2 class="display">{T['band_title']}</h2>
    <p>{T['band_text']}</p>
  </div>
  <div class="actions">
    <a class="btn btn-primary" href="{SITE['subscribe_url']}">{T['subscribe']}</a>
    <a class="btn btn-light" href="{u('/support/')}">{T['support_the_work']}</a>
  </div>
</div></div></section>"""


def chips(active=""):
    items = [(u("/updates/"), T["all"], "")] + [(u(f"/{a['slug']}/"), a["short"], a["slug"]) for a in SITE["areas"]]
    return '<nav class="chips">' + "".join(
        f'<a href="{u}"{" class=on" if k == active else ""}>{esc(t)}</a>' for u, t, k in items) + "</nav>"


def page_home(posts):
    counts = {a["slug"]: sum(1 for p in posts if p["area"]["slug"] == a["slug"]) for a in SITE["areas"]}
    windows = "".join(area_window(a, counts[a["slug"]]) for a in SITE["areas"])
    windows += f"""<a class="area-card cta" href="{u('/support/')}">
  <div class="body">
    <span class="tag">{T['partner']}</span>
    <h3>{T['support_the_work']}</h3>
    <p>{T['support_card']}</p>
    <span class="go">{T['how_to_help']}</span>
  </div>
</a>"""
    latest = ""
    if posts:
        latest = featured(posts[0])
    else:
        latest = f'<div class="empty">{T["first_update"]}</div>'
    content = f"""<div class="intro"><div class="wrap">
  <p class="eyebrow">{T['news_stories']}</p>
  <h1 class="display">{T['home_h1']}</h1>
  <div class="sub">
    <p class="lead">{T['home_lead']}</p>
    <div class="actions">
      <a class="btn btn-primary" href="{SITE['subscribe_url']}">{T['get_newsletter']}</a>
      <a class="btn btn-outline" href="https://pienovangelo.it" rel="noopener">pienovangelo.it</a>
    </div>
  </div>
</div></div>
<section><div class="wrap">
  <div class="section-head">
    <h2 class="display">{T['latest_updates']}</h2>
    <a class="link" href="{u('/updates/')}">{T['all_updates']}</a>
  </div>
  {latest}
</div></section>
<section><div class="wrap">
  <div class="section-head">
    <h2 class="display">{T['updates_by_area']}</h2>
  </div>
  <div class="areas">{windows}</div>
</div></section>
{subscribe_band()}"""
    return layout(SITE["title"], content, active="home")


def page_updates(posts):
    content = f"""<header class="page-head"><div class="wrap">
  <p class="eyebrow">{T['news_stories']}</p>
  <h1 class="display">{T['all_updates_h1']}</h1>
  {chips("")}
</div></header>
<section><div class="wrap">{cards_grid(posts)}</div></section>
{subscribe_band()}"""
    return layout(T["updates_title"], content, active="updates", path="/updates/")


def page_area(a, posts):
    mine = [p for p in posts if p["area"]["slug"] == a["slug"]]
    content = f"""<div class="area-hero"><div class="wrap">
  <div class="window{' has-img' if a.get('image') or video_cover(a) else ''}" {style_c(a)}>
    {video_cover(a) or window_bg(a)}
    <div class="inner">
      <span class="count">{n_updates(len(mine))}</span>
      <h1>{esc(a['name'])}</h1>
      <p>{esc(a['intro'])}</p>
    </div>
  </div>
</div></div>
{area_about(a) if not a.get('video') else ''}
{area_articles(mine)}
{subscribe_band()}
{VIDEO_SCRIPT if video_cover(a) else ''}"""
    return layout(a["name"], content, description=a["intro"], active=a["slug"], path=f"/{a['slug']}/")


def area_articles(mine):
    """Compact list of updates on an area page, as wide as the area window.
    Each shows date, title, excerpt and image; the full text opens in place."""
    if not mine:
        return f'<section><div class="wrap"><div class="empty">{T["first_area_update"]}</div></div></section>'
    out = []
    for p in mine:
        img = f'<img{' class="fit"' if p.get("cover_fit") else ""} src="{esc(p["cover"])}" alt="{esc(p["cover_alt"])}" loading="lazy">' if p["cover"] else ""
        gallery = ("<div class=\"ap-gallery\">" + "".join(
            f'<img src="{esc(g)}" alt="{esc(p["title"])} – {T['photo']} {i + 2}" loading="lazy">'
            for i, g in enumerate(p["gallery"])) + "</div>") if p["gallery"] else ""
        out.append(f"""<article class="area-post{' has-img' if img else ''}" id="{esc(p['slug'])}">
  {f'<div class="ap-img">{img}{gallery}</div>' if img else ''}
  <div class="ap-text">
    <p class="ap-date"><time datetime="{p['date'].isoformat()}">{fmt_date(p['date'])}</time></p>
    <h2 class="ap-title">{esc(p['title'])}</h2>
    <p class="ap-excerpt">{esc(p['excerpt'])}</p>
    <details class="ap-more">
      <summary><span class="open">{T['read_more']}</span><span class="close">{T['close']}</span></summary>
      <div class="prose">{p['html']}</div>
    </details>
  </div>
</article>""")
    script = """<script>{
  const open = () => { const el = location.hash && document.getElementById(location.hash.slice(1));
    const d = el && el.querySelector('details.ap-more'); if (d) { d.open = true; el.scrollIntoView(); } };
  open(); addEventListener('hashchange', open);
  document.querySelectorAll('details.ap-more').forEach(d => d.addEventListener('toggle', () =>
    d.closest('.area-post').classList.toggle('is-open', d.open)));
}</script>"""
    return '<section class="area-posts"><div class="wrap">' + "\n".join(out) + "</div></section>" + script


def area_about(a):
    """Optional presentation (text + video) from content/areas/<slug>.md"""
    path = ROOT / "content" / "areas" / f"{a['slug']}.md"
    if not path.exists():
        return ""
    meta, body = parse_md(tr(path))
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
    eyebrow = (f'<a class="eyebrow" href="{u("/" + a["slug"] + "/")}">{esc(a["name"])}</a>' if a["slug"]
               else f'<p class="eyebrow">{esc(a["name"])}</p>')
    more = [q for q in posts if q is not p and (q["area"]["slug"] == a["slug"] or not a["slug"])][:3]
    more_html = ""
    if more:
        title = T["more_from"].format(esc(a['name'])) if a["slug"] else T["more_updates"]
        more_html = f"""<section><div class="wrap">
  <div class="section-head"><h2 class="display">{title}</h2></div>
  {cards_grid(more)}
</div></section>"""
    back = (f'<a href="{u("/" + a["slug"] + "/")}">{T["back_area"].format(esc(a["name"]))}</a>' if a["slug"]
            else f'<a href="{u("/updates/")}">{T["back_all"]}</a>')
    cover = f'<div class="article-cover">{media(p)}</div>' if p["cover"] else ""
    content = f"""<article>
  <header class="article-head"><div class="narrow">
    {eyebrow}
    <h1 class="display">{esc(p['title'])}</h1>
    <div class="meta">{fmt_date(p['date'])} · {esc(SITE['author'])}</div>
  </div></header>
  {cover}
  <div class="narrow page-body"><div class="prose-card prose">{p['html']}
    <div class="article-foot">{back}<a href="{SITE['subscribe_url']}">{T['get_by_email']}</a></div>
  </div></div>
</article>
{more_html}
{subscribe_band()}"""
    return layout(p["title"], content, description=p["excerpt"], active=a["slug"],
                  image=p["cover"] or None, path=p["path"])


def page_simple(slug, meta, body):
    content = f"""<header class="page-head"><div class="narrow">
  <h1 class="display">{esc(meta.get('title', slug))}</h1>
  {f"<p>{esc(meta['intro'])}</p>" if meta.get('intro') else ""}
</div></header>
<div class="narrow page-body"><div class="prose-card prose">{('<div class="about-map">' + (ROOT / "static" / "img" / "map-italy-puglia.svg").read_text(encoding="utf-8") + '</div>') if slug == 'about' else ''}{render_body(body)}</div></div>
{subscribe_band() if slug not in ('privacy', 'subscribe') else ''}"""
    return layout(meta.get("title", slug), content, description=meta.get("intro"), active=slug, path=f"/{slug}/")


BREVO_FORM = "https://36a940e5.sibforms.com/serve/MUIFAEFtdAN7GjCm-AuY7B6D7oFzLgCFwCa8E13xulCfjhB61wh3tmIzLsTYJvG5nzJ8Sd1IT0sWJjIkB6RRHnLRxuOofGwwzazUZLyCTzaHxdfVvTcX12MKzcmnqlTnZ-w4ATzYlFVNVwaZuxnb7s40ZrW6TCW-ob6SYHI2yrUBExRDkQwaEuzYx54I5PZqCAMry5H_RBGjIq34jA=="


def page_subscribe(meta):
    """Minimal native signup form that posts to the Brevo form (no iframe)."""
    content = f"""<header class="page-head"><div class="narrow">
  <h1 class="display">{esc(meta.get('title', 'Subscribe'))}</h1>
  {f"<p>{esc(meta['intro'])}</p>" if meta.get('intro') else ""}
  <form class="signup" id="signup" method="POST" action="{BREVO_FORM}">
    <label class="sr-only" for="EMAIL">Email</label>
    <input type="email" id="EMAIL" name="EMAIL" placeholder="{T['your_email']}" autocomplete="email" required>
    <input type="text" name="email_address_check" value="" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
    <input type="hidden" name="locale" value="{LANG}">
    <button class="btn btn-primary" type="submit">{T['subscribe']}</button>
    <fieldset class="signup-lang">
      <legend>{T['newsletter_language']}</legend>
      <label><input type="radio" name="LINGUA" value="EN"{' checked' if LANG == 'en' else ''}> English</label>
      <label><input type="radio" name="LINGUA" value="NL"{' checked' if LANG == 'nl' else ''}> Nederlands</label>
    </fieldset>
  </form>
  <p class="signup-msg" id="signup-msg" role="status" aria-live="polite"></p>
  <p class="signup-note">{T['signup_note']} <a href="{u('/privacy/')}">Privacy</a></p>
</div></header>
<script>{{
  const f = document.getElementById('signup'), m = document.getElementById('signup-msg');
  f.addEventListener('submit', async (e) => {{
    e.preventDefault();
    const b = f.querySelector('button'); b.disabled = true; m.className = 'signup-msg';
    try {{
      const r = await fetch(f.action + '?isAjax=1', {{ method: 'POST', body: new FormData(f) }});
      const j = await r.json().catch(() => ({{}}));
      if (!r.ok || j.success === false) throw 0;
      f.hidden = true; m.textContent = {json.dumps(T['signup_ok'])}; m.classList.add('ok');
    }} catch (_) {{
      m.textContent = {json.dumps(T['signup_err'])}; m.classList.add('err');
    }} finally {{ b.disabled = false; }}
  }});
}}</script>"""
    return layout(meta.get("title", "Subscribe"), content, description=meta.get("intro"), active="subscribe", path="/subscribe/")


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
<title>{esc(SITE['title'])}</title><link>{base}{PFX}/</link>
<description>{esc(SITE['description'])}</description><language>{LANG}</language>
{items}</channel></rss>
"""


# ---------- build ----------

def write(rel, text):
    path = OUT / (PFX.lstrip("/") + "/" + rel if PFX else rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    for lang in LANGS:
        set_lang(lang)
        build_lang()
    print(f"Built {', '.join(LANGS)} into {OUT}")


def build_lang():
    posts = load_posts()
    write("index.html", page_home(posts))
    write("updates/index.html", page_updates(posts))
    for a in SITE["areas"]:
        write(f"{a['slug']}/index.html", page_area(a, posts))
    for p in posts:
        write(f"updates/{p['slug']}/index.html", page_post(p, posts))
    for pg in sorted((ROOT / "content" / "pages").glob("*.md")):
        meta, body = parse_md(tr(pg))
        page = page_subscribe(meta) if pg.stem == "subscribe" else page_simple(pg.stem, meta, body)
        write(f"{pg.stem}/index.html", page)
    write("feed.xml", feed(posts))
    if LANG != "en":
        return
    write("404.html", layout("Page not found", """<header class="page-head"><div class="wrap">
  <h1 class="display">Page <em>not found</em></h1><p>The page you are looking for is not here. <a href="/">Go back home</a>.</p>
</div></header>"""))


if __name__ == "__main__":
    main()
