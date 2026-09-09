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
          bg: '#0a0d14',
          card: '#101522',
          border: '#1e293b',
          accent: '#00f0ff',
          glow: '#00f0ff33',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          purple: '#a855f7'
        }
      },
      fontFamily: {
        mono: ['Fira Code', 'Cascadia Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
