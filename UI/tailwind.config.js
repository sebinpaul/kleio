/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-indigo': '#6366f1',
        'brand-purple': '#8b5cf6',
        'brand-cyan': '#06b6d4',
        'brand-emerald': '#10b981',
        'brand-slate-800': '#1e293b',
      },
    },
  },
  plugins: [],
};

