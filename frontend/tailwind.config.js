/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: '#0a0a0f',
        surface: '#12121a',
        card: '#1a1a26',
        border: '#2a2a3d',
        accent: '#00ff88',
        warn: '#ffaa00',
        danger: '#ff3366',
        muted: '#6b6b8a',
        text: '#e8e8f0',
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'fade-up': 'fadeUp 0.5s ease forwards',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        }
      }
    },
  },
  plugins: [],
}