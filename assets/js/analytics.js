/* Custom GA4 event tracking — loaded on every page with defer */
(function () {
  'use strict';

  if (typeof gtag !== 'function') return;

  const postTitle   = document.title.replace(' | Nick McCarty', '').trim();
  const isBlogPost  = !!document.querySelector('article');
  const isSeries    = !!document.querySelector('.series-nav');
  const pageStart   = Date.now();

  /* ── 1. Scroll depth milestones ── */
  const fired = {};
  function scrollPct() {
    const h = document.documentElement;
    const scrollable = Math.max(h.scrollHeight - h.clientHeight, 1);
    return Math.round((window.scrollY / scrollable) * 100);
  }

  window.addEventListener('scroll', function () {
    const pct = scrollPct();
    [25, 50, 75, 100].forEach(function (m) {
      if (!fired[m] && pct >= m) {
        fired[m] = true;
        const elapsed = Math.round((Date.now() - pageStart) / 1000);
        gtag('event', 'scroll_depth', {
          post_title:    postTitle,
          depth_percent: m,
          time_seconds:  elapsed,
          is_series:     isSeries
        });
        /* Article completion: 75 % scroll AND ≥ 90 s on page */
        if (m === 75 && elapsed >= 90) {
          gtag('event', 'article_complete', {
            post_title:       postTitle,
            time_to_complete: elapsed,
            is_series:        isSeries
          });
        }
      }
    });
  }, { passive: true });

  /* ── 2. Time on page (fires on tab close / navigation) ── */
  window.addEventListener('pagehide', function () {
    gtag('event', 'time_on_page', {
      post_title:   postTitle,
      seconds:      Math.round((Date.now() - pageStart) / 1000),
      scroll_depth: scrollPct(),
      is_series:    isSeries
    });
  });

  /* ── 3. Series nav badge clicks ── */
  document.querySelectorAll('.series-badge[href]').forEach(function (el) {
    el.addEventListener('click', function () {
      gtag('event', 'series_nav_click', {
        from_post: postTitle,
        to_badge:  el.textContent.trim(),
        to_url:    el.href
      });
    });
  });

  /* ── 4. Outbound link clicks ── */
  document.querySelectorAll('a[href^="http"]').forEach(function (el) {
    el.addEventListener('click', function () {
      const domain = (new URL(el.href)).hostname;
      if (domain !== window.location.hostname) {
        gtag('event', 'outbound_click', {
          post_title: postTitle,
          url:        el.href,
          domain:     domain,
          link_text:  el.textContent.trim().slice(0, 80)
        });
      }
    });
  });

  /* ── 5. Blog card clicks (blog.html index) ── */
  document.querySelectorAll('.blog-grid a .card').forEach(function (card) {
    card.closest('a').addEventListener('click', function (e) {
      gtag('event', 'blog_card_click', {
        card_title: card.querySelector('h3') ? card.querySelector('h3').textContent.trim() : '',
        to_url:     e.currentTarget.href
      });
    });
  });

  /* ── 6. Theme toggle ── */
  var themeBtn = document.querySelector('.theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      /* color-modes.js toggles data-color-mode after this fires,
         so read current value and report the direction */
      var current = document.documentElement.getAttribute('data-color-mode') || 'dark';
      gtag('event', 'theme_toggle', {
        post_title: postTitle,
        from_theme: current,
        to_theme:   current === 'dark' ? 'light' : 'dark'
      });
    });
  }

  /* ── 7. Internal cross-post navigation (anchor clicks inside articles) ── */
  if (isBlogPost) {
    document.querySelectorAll('article a[href]').forEach(function (el) {
      if (!el.href.startsWith('http')) return;
      var url;
      try { url = new URL(el.href); } catch (e) { return; }
      if (url.hostname === window.location.hostname && url.pathname.includes('/blog/')) {
        el.addEventListener('click', function () {
          gtag('event', 'internal_link_click', {
            from_post: postTitle,
            to_url:    el.href,
            link_text: el.textContent.trim().slice(0, 80)
          });
        });
      }
    });
  }

}());
