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
        canvas: '#0b0f19',
        panel: '#111827',
        panelHover: '#1f2937',
        subtle: '#1e293b',
        borderSubtle: 'rgba(56, 189, 248, 0.15)',
        cyanBrand: '#38bdf8',
        blueBrand: '#0284c7',
        greenComfort: '#22c55e',
        orangeSolar: '#f59e0b',
        redAlert: '#ef4444',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
