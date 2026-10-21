#!/usr/bin/env python3
"""Publish one scheduled article from the private editorial branch into a plain static site."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.etree import ElementTree as ET

BASE = "https://alte-goetter-und-kreuz.github.io"
LOCAL_TZ = ZoneInfo("Europe/Berlin")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def page(article: dict) -> str:
    slug = article["slug"]
    url = f"{BASE}/{slug}/"
    title = article["title"]
    description = article["description"]
    date = article["date"]
    months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
    parsed_date = dt.date.fromisoformat(date)
    published = f"{parsed_date.day}. {months[parsed_date.month - 1]} {parsed_date.year}"
    sources = "\n".join(
        f'<li><a href="{esc(link)}">{esc(label)}</a></li>'
        for link, label in article["sources"]
    )
    body = article["body"]
    internal_links = re.findall(r'href=["\']([^"\']+)', body)
    if len(internal_links) < 3:
        raise ValueError(f"{slug}: fewer than three internal links")
    if any(link.startswith("http") for link in internal_links):
        raise ValueError(f"{slug}: body should only contain relative internal links")
    if not 1 <= len(article["sources"]) <= 2:
        raise ValueError(f"{slug}: expected one or two external sources")
    source_block = f'<div class="sources"><h2>Quellen</h2><ul>{sources}</ul></div>'
    schema = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "name": f"{title} | Zwischen alten Göttern und Kreuz",
        "description": description, "url": url, "datePublished": date,
        "dateModified": date, "inLanguage": "de-DE", "mainEntityOfPage": url,
        "isPartOf": {"@type": "WebSite", "name": "Zwischen alten Göttern und Kreuz", "url": f"{BASE}/"},
    }, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="de"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)} | Zwischen alten Göttern und Kreuz</title>
<meta name="description" content="{esc(description)}"/><meta name="robots" content="index,follow,max-image-preview:large"/>
<link rel="canonical" href="{url}"/><meta name="theme-color" content="#26332d"/>
<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg"/><link rel="stylesheet" href="../assets/style.css"/>
<meta property="og:type" content="article"/><meta property="og:title" content="{esc(title)} | Zwischen alten Göttern und Kreuz"/>
<meta property="og:description" content="{esc(description)}"/><meta property="og:url" content="{url}"/>
<meta property="og:site_name" content="Zwischen alten Göttern und Kreuz"/><meta property="og:locale" content="de_DE"/><meta name="twitter:card" content="summary"/>
<script type="application/ld+json">{schema}</script>
<link rel="alternate" type="application/rss+xml" title="Zwischen alten Göttern und Kreuz – RSS" href="{BASE}/feed.xml"/>
</head><body>
<a class="skip" href="#inhalt">Zum Inhalt</a><div class="topbar"><div class="wrap"><span>Historisches Wissensmagazin</span><span>Quellen statt Legenden</span></div></div>
<header class="site-head"><div class="wrap head-inner">
<a class="brand" href="../"><span class="brand-mark"><svg aria-hidden="true" viewBox="0 0 64 64"><path d="M27 8h10v16h13v10H37v22H27V34H14V24h13z" fill="#a6782d"></path></svg></span><span><strong>Zwischen alten Göttern und Kreuz</strong><span>Geschichte · Symbole · Wandel</span></span></a>
<button class="menu-btn" aria-controls="main-nav" aria-expanded="false" aria-label="Menü öffnen">Menü</button>
<nav id="main-nav" aria-label="Hauptnavigation"><ul><li><a href="../christianisierung/">Christianisierung</a></li><li><a href="../thorhammer-und-kreuz/">Symbole</a></li><li><a href="../runen-und-christentum/">Runen</a></li><li><a href="../quellen/">Quellen</a></li><li><a href="../ueber/">Über uns</a></li></ul></nav></div></header>
<main id="inhalt"><section class="page-hero"><div class="wrap"><div class="breadcrumb"><a href="../">Start</a> / {esc(article['category'])}</div><div class="kicker">{esc(article['category'])}</div><h1>{esc(title)}</h1><p>{esc(description)}</p><div class="article-meta">Veröffentlicht: {esc(published)} · Lesedauer ca. 2–3 Minuten</div></div></section>
<article class="content">{body}{source_block}<div class="article-links"><h3>Weiterlesen</h3><ul><li><a href="../christianisierung/">Christianisierung im Frühmittelalter</a></li><li><a href="../thorhammer-und-kreuz/">Thorhammer und Kreuz</a></li><li><a href="../quellen/">Quellen &amp; Methodik</a></li></ul></div></article></main>
<footer class="footer"><div class="wrap"><div class="footer-grid"><div><h3>Zwischen alten Göttern und Kreuz</h3><p>Ein unabhängiges Wissensmagazin über religiösen Wandel, historische Zeichen und die Frage, was archäologische Quellen tatsächlich erzählen.</p></div><div><h3>Lesen</h3><p><a href="../christianisierung/">Christianisierung</a><br/><a href="../thorhammer-und-kreuz/">Thorhammer &amp; Kreuz</a><br/><a href="../runen-und-christentum/">Runen &amp; Christentum</a><br/><a href="../quellen/">Quellen</a></p></div><div><h3>Rechtliches</h3><p><a href="../impressum/">Impressum</a><br/><a href="../datenschutz/">Datenschutz</a><br/><a href="../feed.xml">RSS-Feed</a></p></div></div><small>© 2026 Zwischen alten Göttern und Kreuz. Historische Einordnung nach nachvollziehbaren Quellen; neue Erkenntnisse können Bewertungen verändern.</small></div></footer>
<script src="../assets/main.js"></script></body></html>'''


def publish(site: Path, drafts: Path, today: dt.date) -> str | None:
    articles = json.loads(drafts.read_text(encoding="utf-8"))
    eligible = sorted((a for a in articles if dt.date.fromisoformat(a["date"]) <= today), key=lambda a: (a["date"], a["slug"]))
    article = next((a for a in eligible if not (site / a["slug"] / "index.html").exists()), None)
    if article is None:
        return None
    slug, date, title = article["slug"], article["date"], article["title"]
    (site / slug).mkdir(parents=True, exist_ok=True)
    (site / slug / "index.html").write_text(page(article), encoding="utf-8")

    homepage = site / "index.html"
    text = homepage.read_text(encoding="utf-8")
    marker = '<div class="kicker">Neue Beiträge</div><h2>Fundstücke, die Fragen öffnen</h2><div class="grid">'
    if marker not in text:
        raise ValueError("Homepage's new articles section was not found")
    card = (f'<article class="card"><div class="tag">{esc(article["category"])}</div>'
            f'<h3>{esc(title)}</h3><p>{esc(article["description"])}</p>'
            f'<a class="more" href="./{slug}/">Artikel lesen →</a></article>')
    homepage.write_text(text.replace(marker, marker + card, 1), encoding="utf-8")

    sitemap = site / "sitemap.xml"
    xml = ET.parse(sitemap)
    root = xml.getroot()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    if not any((node.find(f"{ns}loc").text or "").rstrip("/").endswith("/" + slug) for node in root.findall(f"{ns}url")):
        element = ET.SubElement(root, f"{ns}url")
        ET.SubElement(element, f"{ns}loc").text = f"{BASE}/{slug}/"
        ET.SubElement(element, f"{ns}lastmod").text = date
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    xml.write(sitemap, encoding="utf-8", xml_declaration=True)

    feed_path = site / "feed.xml"
    feed = ET.parse(feed_path)
    channel = feed.getroot().find("channel")
    pubdate = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(9, 0), LOCAL_TZ).strftime("%a, %d %b %Y %H:%M:%S %z")
    item = ET.Element("item")
    for tag, value in (("title", title), ("link", f"{BASE}/{slug}/"), ("guid", f"{BASE}/{slug}/"), ("pubDate", pubdate), ("description", article["description"])):
        ET.SubElement(item, tag).text = value
    first_item = next((i for i, child in enumerate(list(channel)) if child.tag == "item"), len(channel))
    channel.insert(first_item, item)
    last_build = channel.find("lastBuildDate")
    if last_build is not None:
        last_build.text = dt.datetime.now(dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    feed.write(feed_path, encoding="utf-8", xml_declaration=True)
    return f"Published {slug} ({date})"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default=".")
    parser.add_argument("--drafts", default="_drafts/articles.json")
    parser.add_argument("--today", default=None, help="Override local publication date for testing")
    args = parser.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(LOCAL_TZ).date()
    result = publish(Path(args.site), Path(args.drafts), today)
    print(result or "No due article to publish")
