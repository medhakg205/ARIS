// ============================================================
// ARIS — Professional Theme Engine (v3.0.0)
// Supports Dark, Light, and System themes with local persistence
// ============================================================

import { useState, useEffect, useCallback } from 'react';

export type ThemeMode = 'dark' | 'light' | 'system';
export type ResolvedTheme = 'dark' | 'light';

const THEME_STORAGE_KEY = 'aris-theme-mode';

export function getInitialTheme(): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'dark' || saved === 'light' || saved === 'system') {
      return saved;
    }
  } catch (_) {
    // LocalStorage unavailable
  }
  return 'dark'; // Default to engineering dark theme
}

export function useTheme() {
  const [themeMode, setThemeModeState] = useState<ThemeMode>(getInitialTheme);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('dark');

  const applyTheme = useCallback((mode: ThemeMode) => {
    let effective: ResolvedTheme = 'dark';
    if (mode === 'system') {
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      effective = prefersDark ? 'dark' : 'light';
    } else {
      effective = mode;
    }

    setResolvedTheme(effective);
    const root = document.documentElement;

    if (effective === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
      root.setAttribute('data-theme', 'dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
      root.setAttribute('data-theme', 'light');
      root.style.colorScheme = 'light';
    }
  }, []);

  const setThemeMode = useCallback((mode: ThemeMode) => {
    setThemeModeState(mode);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (_) {
      // Ignored
    }
    applyTheme(mode);
  }, [applyTheme]);

  useEffect(() => {
    applyTheme(themeMode);

    if (themeMode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => applyTheme('system');
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [themeMode, applyTheme]);

  return {
    themeMode,
    resolvedTheme,
    setThemeMode,
    toggleTheme: () => setThemeMode(resolvedTheme === 'dark' ? 'light' : 'dark'),
  };
}
