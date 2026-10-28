import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#08080a',
          900: '#0d0d12',
          850: '#14141c',
          800: '#1c1c27',
          700: '#2c2c3c',
        },
        ectoplasm: {
          500: '#10b981',
          400: '#34d399',
          300: '#6ee7b7',
        },
        spectral: {
          500: '#8b5cf6',
          400: '#a78bfa',
          300: '#c4b5fd',
        },
        marigold: {
          500: '#f59e0b',
          400: '#fbbf24',
          300: '#fcd34d',
        },
        tactical: {
          border: '#272738',
          text: '#94a3b8',
        },
      },
      boxShadow: {
        'tactile-dark': '3px 3px 0 #000000',
        'tactile-glow': '0 0 15px rgba(16, 185, 129, 0.15)',
        'tactile-candle': '0 0 20px rgba(245, 158, 11, 0.15)',
      },
    },
  },
  plugins: [],
};

export default config;
