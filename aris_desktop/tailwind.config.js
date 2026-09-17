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
        aris: {
          bg: '#080a10',
          card: '#0e121b',
          cardHover: '#141a26',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          accent: '#3b82f6',
          glow: 'rgba(59, 130, 246, 0.15)',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#f43f5e',
          purple: '#8b5cf6',
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
