import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#1e293b',
        accent: '#22c55e',
        background: '#0f172a',
        foreground: '#f8fafc',
        muted: '#64748b',
        border: '#334155',
        card: '#1e293b',
      },
    },
  },
  plugins: [],
};

export default config;
