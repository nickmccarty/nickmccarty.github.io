'use strict';
(function () {
  function gtagEvent(name, params) {
    if (typeof gtag !== 'function') return;
    gtag('event', name, params);
  }

  // Scroll depth — fires once per milestone per page load
  function initScrollDepth(context) {
    const milestones = [25, 50, 75, 90];
    const reached    = new Set();
    let ticking      = false;

    function depth() {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      return total > 0 ? Math.floor((window.scrollY / total) * 100) : 0;
    }

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        const pct = depth();
        milestones.forEach(function (m) {
          if (pct >= m && !reached.has(m)) {
            reached.add(m);
            gtagEvent('scroll_depth', { percent_scrolled: m, page_context: context });
            if (m === 90 && context === 'blog_post') {
              gtagEvent('reading_complete', { page_path: window.location.pathname });
            }
          }
        });
        ticking = false;
      });
    }, { passive: true });
  }

  document.addEventListener('DOMContentLoaded', function () {
    const isBlogPost = window.location.pathname.includes('/blog/') &&
                       window.location.pathname.endsWith('.html');
    initScrollDepth(isBlogPost ? 'blog_post' : 'page');

    // Outbound link clicks
    document.querySelectorAll('a[target="_blank"]').forEach(function (link) {
      link.addEventListener('click', function () {
        gtagEvent('outbound_click', {
          link_url:  link.href,
          link_text: link.textContent.trim().slice(0, 50)
        });
      });
    });
  });
}());
