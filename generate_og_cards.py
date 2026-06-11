#!/usr/bin/env python3
"""
Generate per-post OG card images via Jinja2 + Playwright.

Usage:
    python generate_og_cards.py                   # all posts
    python generate_og_cards.py blog/X.html       # one or more specific posts
    python generate_og_cards.py --preview         # render HTML only, skip Playwright
    python generate_og_cards.py --no-update       # screenshot but skip updating post meta
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
BLOG_DIR = ROOT / "blog"
OG_DIR = ROOT / "assets" / "images" / "og"
TEMPLATE_NAME = "og_post_card.html.j2"
SITE_URL = "https://nickmccarty.me"


# ── helpers ──────────────────────────────────────────────────────────────────

def title_size(title: str) -> str:
    n = len(title)
    if n <= 35: return "lg"
    if n <= 55: return "md"
    if n <= 75: return "sm"
    return "xs"


def fmt_date(iso: str) -> str:
    iso = iso.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        return f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    except ValueError:
        return iso[:10]


def extract(html_path: Path) -> dict | None:
    """Return post metadata dict, or None if the page isn't a dated article."""
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")

    # Must have a published date to be a real article
    date_meta = soup.find("meta", property="article:published_time")
    if not date_meta:
        return None

    def og(prop):
        tag = soup.find("meta", property=prop)
        return tag["content"].strip() if tag and tag.get("content") else ""

    title = og("og:title") or (soup.find("title") or {}).get_text("").strip()
    description = og("og:description") or og("description")

    # Truncate description so it fits 3 lines at ~16.5px in a 576px column
    if len(description) > 220:
        description = description[:217].rsplit(" ", 1)[0] + "…"

    published = fmt_date(date_meta["content"])

    # Keywords + section from JSON-LD
    keywords: list[str] = []
    section = ""
    ld_tag = soup.find("script", type="application/ld+json")
    if ld_tag:
        try:
            ld = json.loads(ld_tag.get_text())
            raw_kw = ld.get("keywords", "")
            if raw_kw:
                keywords = [k.strip()[:22] for k in raw_kw.split(",") if k.strip()][:4]
            section = ld.get("articleSection", "")
        except (json.JSONDecodeError, TypeError):
            pass

    slug = html_path.stem
    og_image_url = f"{SITE_URL}/assets/images/og/{slug}.png"

    return {
        "title": title,
        "description": description,
        "published": published,
        "keywords": keywords,
        "section": section,
        "slug": slug,
        "title_size": title_size(title),
        "og_image_url": og_image_url,
    }


def render(data: dict, env: Environment) -> str:
    return env.get_template(TEMPLATE_NAME).render(**data)


def screenshot(card_html: Path, out_png: Path, page) -> None:
    url = "file:///" + card_html.as_posix()
    page.goto(url, wait_until="domcontentloaded")
    page.screenshot(path=str(out_png), clip={"x": 0, "y": 0, "width": 1200, "height": 630})


def update_post(html_path: Path, og_image_url: str) -> None:
    """Rewrite og:image, twitter:image, and JSON-LD image.url in a post file."""
    text = html_path.read_text(encoding="utf-8")

    def swap(pattern, replacement):
        return re.sub(pattern, replacement, text)

    text = re.sub(
        r'(<meta property="og:image" content=")[^"]*(")',
        rf'\g<1>{og_image_url}\g<2>',
        text,
    )
    text = re.sub(
        r'(<meta name="twitter:image" content=")[^"]*(")',
        rf'\g<1>{og_image_url}\g<2>',
        text,
    )
    # JSON-LD image object  "image":{"@type":"ImageObject","url":"..."
    text = re.sub(
        r'("image":\{"@type":"ImageObject","url":")[^"]*(")',
        rf'\g<1>{og_image_url}\g<2>',
        text,
    )
    html_path.write_text(text, encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    paths = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]

    preview   = "--preview"   in flags
    no_update = "--no-update" in flags

    posts = paths if paths else sorted(BLOG_DIR.glob("*.html"))

    OG_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(OG_DIR)), autoescape=True)

    ok = skipped = errors = 0

    if preview:
        for post_path in posts:
            try:
                data = extract(post_path)
                if data is None:
                    skipped += 1
                    continue
                html_out = OG_DIR / f"{data['slug']}.html"
                html_out.write_text(render(data, env), encoding="utf-8")
                print(f"  preview  {html_out}")
                ok += 1
            except Exception as exc:
                print(f"  ERR {post_path.name}: {exc}", file=sys.stderr)
                errors += 1
    else:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            for post_path in posts:
                try:
                    data = extract(post_path)
                    if data is None:
                        skipped += 1
                        continue
                    html_out = OG_DIR / f"{data['slug']}.html"
                    html_out.write_text(render(data, env), encoding="utf-8")
                    png_out = OG_DIR / f"{data['slug']}.png"
                    screenshot(html_out, png_out, page)
                    if not no_update:
                        update_post(post_path, data["og_image_url"])
                    print(f"  ok  {data['slug']}")
                    ok += 1
                except Exception as exc:
                    print(f"  ERR {post_path.name}: {exc}", file=sys.stderr)
                    errors += 1
            browser.close()

    print(f"\n{ok} generated, {skipped} skipped (no date), {errors} errors")


if __name__ == "__main__":
    main()
