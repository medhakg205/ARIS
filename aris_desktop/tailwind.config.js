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
          bg: '#181b1f',
          surface: '#1e2229',
          card: '#22272e',
          cardHover: '#282e38',
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          accent: '#00878a',
          accentHover: '#00979d',
          glow: 'rgba(0, 135, 138, 0.15)',
          success: '#00878a',
          warning: '#e5a00d',
          danger: '#e05252',
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
