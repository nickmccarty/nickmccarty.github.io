#!/usr/bin/env python3
"""
Enhance schema across all blog posts and sitemap.xml:

  1. Add speakable to every BlogPosting JSON-LD
  2. Add about + mentions to every BlogPosting JSON-LD
  3. Inject BreadcrumbList script tag where missing
  4. Add image:image extensions to sitemap.xml

Usage:
    python enhance_schema.py
"""

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).parent
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://nickmccarty.me"

SPEAKABLE = {
    "@type": "SpeakableSpecification",
    "cssSelector": ["h1", ".subtitle"],
}


# ── per-post JSON-LD enhancement ──────────────────────────────────────────────

def patch_blogposting(html: str, slug: str, title: str, post_url: str) -> str:
    """Inject speakable + about + mentions into the BlogPosting JSON-LD block."""

    # Regex targets the BlogPosting ld+json block (single-line JSON)
    ld_pat = re.compile(
        r'(<script type="application/ld\+json">)'
        r'(\{[^<]*?"@type":"BlogPosting"[^<]*?\})'
        r'(</script>)',
        re.DOTALL,
    )
    m = ld_pat.search(html)
    if not m:
        return html

    try:
        ld = json.loads(m.group(2))
    except json.JSONDecodeError:
        return html

    changed = False

    # 1. speakable
    if "speakable" not in ld:
        ld["speakable"] = SPEAKABLE
        changed = True

    # 2. about + mentions (derived from articleSection + keywords)
    if "about" not in ld:
        section = ld.get("articleSection", "")
        raw_kw  = ld.get("keywords", "")
        kws     = [k.strip() for k in raw_kw.split(",") if k.strip()] if raw_kw else []

        if section:
            ld["about"] = {"@type": "Thing", "name": section}
            changed = True
        if kws:
            ld["mentions"] = [{"@type": "Thing", "name": k} for k in kws[:5]]
            changed = True

    if not changed:
        return html

    new_ld = json.dumps(ld, separators=(",", ":"), ensure_ascii=False)
    return html[:m.start()] + m.group(1) + new_ld + m.group(3) + html[m.end():]


def inject_breadcrumb(html: str, title: str, post_url: str) -> str:
    """Add a BreadcrumbList script tag before </head> if not already present."""
    if "BreadcrumbList" in html:
        return html

    crumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",  "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Blog",  "item": f"{SITE_URL}/blog.html"},
            {"@type": "ListItem", "position": 3, "name": title,   "item": post_url},
        ],
    }
    tag = (
        f'  <script type="application/ld+json">'
        f'{json.dumps(crumb, separators=(",", ":"), ensure_ascii=False)}'
        f"</script>\n"
    )
    return html.replace("</head>", tag + "</head>", 1)


# ── sitemap image extension ───────────────────────────────────────────────────

def enhance_sitemap(post_meta: list[dict]) -> None:
    sitemap_path = ROOT / "sitemap.xml"
    text = sitemap_path.read_text(encoding="utf-8")

    # Add image namespace to root element if missing
    if "xmlns:image" not in text:
        text = text.replace(
            'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '     xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"',
        )

    lookup = {p["slug"]: p for p in post_meta}

    def replace_url_block(m: re.Match) -> str:
        block = m.group(0)
        loc_m = re.search(r"<loc>([^<]+)</loc>", block)
        if not loc_m:
            return block
        loc = loc_m.group(1)

        # Extract slug from the blog URL
        slug_m = re.search(r"/blog/([^.]+)\.html", loc)
        if not slug_m:
            return block

        slug = slug_m.group(1)
        post = lookup.get(slug)
        if not post:
            return block

        png_path = ROOT / "assets" / "images" / "og" / f"{slug}.png"
        if not png_path.exists():
            return block

        if "<image:image>" in block:
            return block  # already has it

        image_block = (
            f"    <image:image>\n"
            f"      <image:loc>{xml_escape(post['og_image_url'])}</image:loc>\n"
            f"      <image:title>{xml_escape(post['title'])}</image:title>\n"
            f"    </image:image>\n"
        )
        # Insert before closing </url>
        return block.replace("  </url>", image_block + "  </url>", 1)

    text = re.sub(r"  <url>.*?  </url>", replace_url_block, text, flags=re.DOTALL)
    sitemap_path.write_text(text, encoding="utf-8")


# ── helpers ───────────────────────────────────────────────────────────────────

def get_title_and_url(html_path: Path) -> tuple[str, str]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'property="og:title" content="([^"]+)"', text)
    title = m.group(1).strip() if m else html_path.stem
    url = f"{SITE_URL}/blog/{html_path.name}"
    return title, url


def is_dated_article(html_path: Path) -> bool:
    return bool(re.search(
        r"article:published_time",
        html_path.read_text(encoding="utf-8", errors="ignore"),
    ))


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    posts = [p for p in sorted(BLOG_DIR.glob("*.html")) if is_dated_article(p)]
    post_meta: list[dict] = []

    ld_patched = breadcrumb_added = 0

    for post_path in posts:
        html = post_path.read_text(encoding="utf-8")
        title, url = get_title_and_url(post_path)
        slug = post_path.stem

        original = html
        html = patch_blogposting(html, slug, title, url)
        html = inject_breadcrumb(html, title, url)

        if html != original:
            post_path.write_text(html, encoding="utf-8")
            if patch_blogposting.__doc__ and "speakable" in html:
                ld_patched += 1
            if "BreadcrumbList" in html and "BreadcrumbList" not in original:
                breadcrumb_added += 1

        post_meta.append({
            "slug": slug,
            "title": title,
            "og_image_url": f"{SITE_URL}/assets/images/og/{slug}.png",
        })

    enhance_sitemap(post_meta)

    print(f"BlogPosting JSON-LD patched : {len(posts)} posts")
    print(f"BreadcrumbList injected     : {breadcrumb_added} posts")
    print(f"Sitemap image extensions    : added to sitemap.xml")


if __name__ == "__main__":
    main()
