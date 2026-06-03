"""
Build search-index.json from all blog post HTML files.
Run from the nickmccarty.github.io root:
    python build_search_index.py
"""
import json, re
from html.parser import HTMLParser
from pathlib import Path

BLOG_DIR = Path('blog')
OUT      = Path('search-index.json')
BODY_CAP = 8_000    # chars of body text to store per post


class TextExtractor(HTMLParser):
    SKIP = {'script', 'style', 'nav', 'footer', 'noscript', 'head'}

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            s = data.strip()
            if s:
                self._buf.append(s)

    def text(self):
        return re.sub(r'\s+', ' ', ' '.join(self._buf)).strip()


def _jld(html, field):
    m = re.search(rf'"{re.escape(field)}"\s*:\s*"([^"]+)"', html)
    return m.group(1) if m else ''


def _meta(html, name):
    m = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]+)"', html)
    if not m:
        m = re.search(rf'<meta\s+content="([^"]+)"\s+name="{re.escape(name)}"', html)
    return m.group(1) if m else ''


entries = []

for path in sorted(BLOG_DIR.glob('*.html')):
    html = path.read_text(encoding='utf-8', errors='replace')

    title = _jld(html, 'headline')
    if not title:
        m = re.search(r'<title>([^<]+)</title>', html)
        title = m.group(1).split('|')[0].strip() if m else path.stem

    date       = _jld(html, 'datePublished')
    desc       = _meta(html, 'description') or _jld(html, 'description')
    section    = _jld(html, 'articleSection')

    ex = TextExtractor()
    ex.feed(html)
    body = ex.text()[:BODY_CAP]

    entries.append({
        's': path.name,   # slug
        't': title,       # title
        'd': date,        # datePublished
        'c': section,     # category/section
        'p': desc,        # description (preview)
        'b': body,        # body text
    })

OUT.write_text(
    json.dumps(entries, ensure_ascii=False, separators=(',', ':')),
    encoding='utf-8',
)
print(f"Wrote {len(entries)} entries -> {OUT}  ({OUT.stat().st_size // 1024} KB)")
