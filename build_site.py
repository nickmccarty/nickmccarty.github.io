"""
build_site.py — regenerate all derived site artifacts.

Run from the nickmccarty.github.io root:
    python build_site.py

Outputs:
    search-index.json   — full-text search index for the blog
    sitemap.xml         — canonical URL list for Google Search Console
    llms.txt            — LLM-friendly site manifest (llmstxt.org spec)

Side effects:
    Injects Google Analytics into any blog post that is missing it.
"""
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL   = "https://nickmccarty.me"
GA_ID      = "G-YT69KZ91W7"
BLOG_DIR   = Path("blog")
TODAY      = date.today().isoformat()
BODY_CAP   = 8_000

GA_SNIPPET = (
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
    f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
    f'gtag(\'js\',new Date());gtag(\'config\',\'{GA_ID}\');</script>\n'
    f'</head>'
)


# ── HTML text extractor ───────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "noscript", "head"}

    def __init__(self):
        super().__init__()
        self._d = 0
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._d += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._d:
            self._d -= 1

    def handle_data(self, data):
        if not self._d:
            s = data.strip()
            if s:
                self._buf.append(s)

    def text(self):
        return re.sub(r"\s+", " ", " ".join(self._buf)).strip()


# ── Helpers ───────────────────────────────────────────────────────────────────
def jld(html, field):
    m = re.search(rf'"{re.escape(field)}"\s*:\s*"([^"]+)"', html)
    return m.group(1) if m else ""


def meta_tag(html, name):
    m = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]+)"', html)
    if not m:
        m = re.search(rf'<meta\s+content="([^"]+)"\s+name="{re.escape(name)}"', html)
    return m.group(1) if m else ""


def read_post(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    title   = jld(html, "headline") or path.stem
    date_   = jld(html, "datePublished")
    section = jld(html, "articleSection")
    desc    = meta_tag(html, "description") or jld(html, "description")
    ex = TextExtractor()
    ex.feed(html)
    body = ex.text()[:BODY_CAP]
    return dict(s=path.name, t=title, d=date_, c=section, p=desc, b=body,
                _html=html, _date=date_ or TODAY)


# ── Load all posts ────────────────────────────────────────────────────────────
posts = [read_post(p) for p in sorted(BLOG_DIR.glob("*.html"))
         if not p.stem.endswith("-embed")]
print(f"Loaded {len(posts)} posts")


# ── 1. Search index ───────────────────────────────────────────────────────────
index_data = [{k: v for k, v in p.items() if not k.startswith("_")} for p in posts]
Path("search-index.json").write_text(
    json.dumps(index_data, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
sz = Path("search-index.json").stat().st_size // 1024
print(f"search-index.json  {len(posts)} entries  {sz} KB")


# ── 1b. keywords.json ─────────────────────────────────────────────────────────
kw_map = {}
for p in posts:
    raw = jld(p["_html"], "keywords")
    if not raw:
        continue
    kws = [k.strip() for k in raw.split(",") if k.strip()][:3]
    if kws:
        kw_map[p["s"]] = kws
Path("keywords.json").write_text(
    json.dumps(kw_map, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print(f"keywords.json      {len(kw_map)} posts tagged")


# ── 2. Sitemap ────────────────────────────────────────────────────────────────
STATIC = [
    ("",             1.0, "monthly",  TODAY),
    ("about.html",   0.9, "monthly",  TODAY),
    ("blog.html",    0.9, "weekly",   TODAY),
    ("contact.html", 0.7, "yearly",   TODAY),
]

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

for path, pri, freq, mod in STATIC:
    url = f"{BASE_URL}/{path}"
    lines += [
        "  <url>",
        f"    <loc>{url}</loc>",
        f"    <lastmod>{mod}</lastmod>",
        f"    <changefreq>{freq}</changefreq>",
        f"    <priority>{pri:.1f}</priority>",
        "  </url>",
    ]

for p in posts:
    if (BLOG_DIR / p["s"]).stat().st_size > 500_000:
        continue  # skip heavyweight notebook exports — Google can't index them
    url = f"{BASE_URL}/blog/{p['s']}"
    mod = p["_date"]
    # Higher priority for series/analysis posts
    pri = 0.8 if p["c"] in ("Agentic Harness Engineering", "Analysis") else 0.7
    lines += [
        "  <url>",
        f"    <loc>{url}</loc>",
        f"    <lastmod>{mod}</lastmod>",
        "    <changefreq>monthly</changefreq>",
        f"    <priority>{pri:.1f}</priority>",
        "  </url>",
    ]

lines.append("</urlset>")
Path("sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"sitemap.xml        {len(STATIC) + len(posts)} URLs")


# ── 3. llms.txt ───────────────────────────────────────────────────────────────
# Group posts by section for the manifest
from collections import defaultdict
by_section = defaultdict(list)
for p in posts:
    by_section[p["c"] or "Other"].append(p)

# Curated key posts for the main listing
KEY_POSTS = [
    "harness-thesis.html",
    "the-wiggum-loop.html",
    "agent-pipeline.html",
    "inference-shim.html",
    "memory-view.html",
    "autoresearch-view.html",
    "eval-suite.html",
    "lit-review-skill.html",
    "osint-skill.html",
    "agentic-design-patterns.html",
    "panel.html",
    "skillopt-shipped.html",
    "convergence-detectors-shipped.html",
    "gepa-autoresearch.html",
    "security-patterns.html",
    "context-engineering.html",
    "harness-data-model.html",
    "fred-bea-tools.html",
    "perplexity-vs-harness.html",
    "alt-data-pipeline.html",
]

post_by_slug = {p["s"]: p for p in posts}

llms_lines = [
    "# Nick McCarty",
    "",
    "> Technical blog covering agentic systems engineering, local LLM inference on consumer hardware,",
    "> self-improving prompt optimization loops, multi-agent orchestration, computer vision,",
    "> and ML research. All harness work runs on a local RTX 5000 Ada with llama.cpp / vLLM backends.",
    "",
    "## Main pages",
    "",
    f"- [Blog index]({BASE_URL}/blog.html): Full post listing with category filter and full-text search",
    f"- [About]({BASE_URL}/about.html): Background, current work, and contact",
    "",
    "## Key posts — Agentic Harness Engineering",
    "",
]

for slug in KEY_POSTS:
    p = post_by_slug.get(slug)
    if not p:
        continue
    desc = p["p"].split(".")[0].rstrip() if p["p"] else ""
    llms_lines.append(f"- [{p['t']}]({BASE_URL}/blog/{slug}): {desc}")

llms_lines += [
    "",
    "## All posts by section",
    "",
]

for section, section_posts in sorted(by_section.items()):
    llms_lines.append(f"### {section}")
    llms_lines.append("")
    for p in sorted(section_posts, key=lambda x: x["_date"], reverse=True):
        llms_lines.append(f"- [{p['t']}]({BASE_URL}/blog/{p['s']})")
    llms_lines.append("")

llms_lines += [
    "## Site notes",
    "",
    "- All inference runs locally (no cloud API for the core harness pipeline)",
    "- Posts are generated by the harness itself via /lit-review and research skills,",
    "  then edited and published manually",
    "- Search index at /search-index.json (100 posts, ~740 KB)",
    "- Sitemap at /sitemap.xml",
]

Path("llms.txt").write_text("\n".join(llms_lines) + "\n", encoding="utf-8")
print(f"llms.txt           {len(llms_lines)} lines")


# ── 4. Inject GA into posts missing it ───────────────────────────────────────
ga_pattern = re.compile(re.escape(GA_ID))
fixed = 0
for p in posts:
    html = p["_html"]
    path = BLOG_DIR / p["s"]
    # Skip data-heavy files (> 500 KB) -- notebook exports / SVG dumps
    if path.stat().st_size > 500_000:
        continue
    if ga_pattern.search(html):
        continue
    # Inject before </head>
    new_html = html.replace("</head>", GA_SNIPPET, 1)
    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        print(f"  + GA injected   {p['s']}")
        fixed += 1

if fixed == 0:
    print("GA injection       all posts already have GA")
else:
    print(f"GA injection       {fixed} posts updated")

print("\nDone.")
