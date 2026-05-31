'use strict';
const fs   = require('fs');
const path = require('path');

const ROOT     = path.join(__dirname, '..');
const BLOG_DIR = path.join(ROOT, 'blog');
const BASE_URL = 'https://nickmccarty.me';
const TODAY    = new Date().toISOString().slice(0, 10);

const staticPages = [
  { url: '/',             lastmod: TODAY,       changefreq: 'monthly', priority: 1.0 },
  { url: '/about.html',   lastmod: TODAY,       changefreq: 'monthly', priority: 0.9 },
  { url: '/blog.html',    lastmod: TODAY,       changefreq: 'weekly',  priority: 0.9 },
  { url: '/contact.html', lastmod: TODAY,       changefreq: 'yearly',  priority: 0.7 },
];

const blogPages = fs
  .readdirSync(BLOG_DIR)
  .filter(f => f.endsWith('.html'))
  .sort()
  .map(file => {
    const html = fs.readFileSync(path.join(BLOG_DIR, file), 'utf-8');
    let lastmod = TODAY;
    const m = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
    if (m) {
      try {
        const ld = JSON.parse(m[1]);
        if (ld.dateModified)   lastmod = ld.dateModified.slice(0, 10);
        else if (ld.datePublished) lastmod = ld.datePublished.slice(0, 10);
      } catch (_) {}
    }
    return { url: `/blog/${file}`, lastmod, changefreq: 'monthly', priority: 0.85 };
  });

const pages = [...staticPages, ...blogPages];

const urlNodes = pages.map(p =>
  `  <url>\n    <loc>${BASE_URL}${p.url}</loc>\n    <lastmod>${p.lastmod}</lastmod>\n    <changefreq>${p.changefreq}</changefreq>\n    <priority>${p.priority.toFixed(1)}</priority>\n  </url>`
).join('\n');

const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlNodes}\n</urlset>\n`;

fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), xml, 'utf-8');
console.log(`sitemap.xml written — ${pages.length} URLs (${blogPages.length} blog posts)`);
