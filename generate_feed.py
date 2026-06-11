#!/usr/bin/env python3
"""
Generate feed.xml (RSS 2.0) from blog post metadata.

Usage:
    python generate_feed.py
"""

import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://nickmccarty.me"
FEED_OUT = ROOT / "feed.xml"
MAX_ITEMS = 50


def extract(html_path: Path) -> dict | None:
    text = html_path.read_text(encoding="utf-8", errors="ignore")

    date_m = re.search(r'article:published_time.*?content="([^"]+)"', text)
    if not date_m:
        return None

    def og(prop):
        m = re.search(rf'property="{re.escape(prop)}" content="([^"]+)"', text)
        return m.group(1).strip() if m else ""

    title = og("og:title")
    description = og("og:description") or og("description")
    og_image = og("og:image")

    keywords: list[str] = []
    section = ""
    ld_m = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
    if ld_m:
        try:
            ld = json.loads(ld_m.group(1))
            raw_kw = ld.get("keywords", "")
            if raw_kw:
                keywords = [k.strip() for k in raw_kw.split(",") if k.strip()]
            section = ld.get("articleSection", "")
        except (json.JSONDecodeError, TypeError):
            pass

    iso = date_m.group(1).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.now(timezone.utc)

    return {
        "title": title,
        "description": description,
        "url": f"{SITE_URL}/blog/{html_path.name}",
        "og_image": og_image,
        "published": dt,
        "rfc822": format_datetime(dt),
        "keywords": keywords,
        "section": section,
        "slug": html_path.stem,
    }


def item_xml(post: dict) -> str:
    cats = "".join(f"    <category>{escape(k)}</category>\n" for k in post["keywords"][:5])
    enclosure = (
        f'    <enclosure url="{escape(post["og_image"])}" type="image/png" length="0"/>\n'
        if post["og_image"] else ""
    )
    return (
        f"  <item>\n"
        f"    <title>{escape(post['title'])}</title>\n"
        f"    <link>{escape(post['url'])}</link>\n"
        f"    <guid isPermaLink=\"true\">{escape(post['url'])}</guid>\n"
        f"    <pubDate>{post['rfc822']}</pubDate>\n"
        f"    <description>{escape(post['description'])}</description>\n"
        f"    <author>nickmccarty0@gmail.com (Nick McCarty)</author>\n"
        f"{cats}"
        f"{enclosure}"
        f"  </item>"
    )


def main() -> None:
    posts = []
    for p in BLOG_DIR.glob("*.html"):
        data = extract(p)
        if data:
            posts.append(data)

    posts.sort(key=lambda x: x["published"], reverse=True)
    posts = posts[:MAX_ITEMS]

    build_date = format_datetime(datetime.now(timezone.utc))
    last_pub   = posts[0]["rfc822"] if posts else build_date

    items = "\n".join(item_xml(p) for p in posts)

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Nick McCarty</title>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Data science, ML/AI, computer vision, and agentic systems — by Nick McCarty.</description>
    <language>en-us</language>
    <managingEditor>nickmccarty0@gmail.com (Nick McCarty)</managingEditor>
    <webMaster>nickmccarty0@gmail.com (Nick McCarty)</webMaster>
    <lastBuildDate>{build_date}</lastBuildDate>
    <pubDate>{last_pub}</pubDate>
    <ttl>1440</ttl>
    <image>
      <url>{SITE_URL}/assets/images/og-default.png</url>
      <title>Nick McCarty</title>
      <link>{SITE_URL}</link>
    </image>
{items}
  </channel>
</rss>
"""
    FEED_OUT.write_text(feed, encoding="utf-8")
    print(f"Wrote {len(posts)} items to {FEED_OUT}")


if __name__ == "__main__":
    main()
