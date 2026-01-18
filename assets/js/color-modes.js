/**
 * Theme Toggle - Dark/Light Mode
 * Persists preference to localStorage and respects system preference
 */

(() => {
  'use strict';

  // Get stored theme or default to system preference
  const getStoredTheme = () => localStorage.getItem('theme');
  const setStoredTheme = (theme) => localStorage.setItem('theme', theme);

  const getPreferredTheme = () => {
    const stored = getStoredTheme();
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  };

  // Apply theme to document
  const setTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
  };

  // Initialize theme immediately (before DOM loads to prevent flash)
  setTheme(getPreferredTheme());

  // Handle toggle button click
  const toggleTheme = () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
    setStoredTheme(next);
  };

  // Listen for system preference changes
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    // Only auto-switch if user hasn't manually set a preference
    if (!getStoredTheme()) {
      setTheme(e.matches ? 'light' : 'dark');
    }
  });

  // Setup toggle button when DOM is ready
  window.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.querySelector('.theme-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleTheme);
    }
  });
})();
