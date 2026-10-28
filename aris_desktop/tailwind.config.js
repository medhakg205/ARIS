/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        app: 'var(--bg-app)',
        card: 'var(--bg-card)',
        surface: 'var(--bg-surface)',
        sidebar: 'var(--bg-sidebar)',
        header: 'var(--bg-header)',
        border: 'var(--border-color)',
        hover: 'var(--bg-card-hover)',
        fg: 'var(--text-primary)',
        muted: 'var(--text-muted)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        accent: {
          cyan: 'var(--accent-cyan)',
          green: 'var(--accent-green)',
          amber: 'var(--accent-amber)',
          red: 'var(--accent-red)',
          purple: 'var(--accent-purple)',
        },
        aris: {
          bg: '#12151a',
          surface: '#161920',
          card: '#1a1e26',
          cardHover: '#222732',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          accent: '#00878a',
          accentHover: '#00979d',
          glow: 'rgba(0, 135, 138, 0.15)',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          muted: '#8b949e',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        samsung: ['"Samsung Sharp Sans"', '"Plus Jakarta Sans"', 'sans-serif'],
        heading: ['"Samsung Sharp Sans"', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Cascadia Code', 'Consolas', 'monospace']
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}
