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
          bg: '#07090e',
          card: '#0d111a',
          cardHover: '#131926',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          accent: '#00e5ff',
          glow: 'rgba(0, 229, 255, 0.25)',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#f43f5e',
          purple: '#a855f7',
        }
      },
      fontFamily: {
        sans: ['"Samsung Sharp Sans"', '"SamsungOne"', '"Plus Jakarta Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        samsung: ['"Samsung Sharp Sans"', '"SamsungOne"', 'sans-serif'],
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
