/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /*
         * THEME-AWARE ENGINEERING PALETTES (visual polish pass)
         * =====================================================
         * Many stage components express surfaces/borders/inputs with the
         * Tailwind `slate` scale. To keep ONE component geometry across both
         * themes (dark: navy surfaces; light: crisp white panels), the slate
         * shades used by the app are routed through CSS channel variables
         * (`R G B`) that each theme maps to its own values in index.css.
         * Dark theme reproduces the original Tailwind slate values exactly,
         * so the existing dark aesthetic is unchanged.
         */
        slate: {
          100: 'rgb(var(--ts-slate-100) / <alpha-value>)',
          200: 'rgb(var(--ts-slate-200) / <alpha-value>)',
          300: 'rgb(var(--ts-slate-300) / <alpha-value>)',
          400: 'rgb(var(--ts-slate-400) / <alpha-value>)',
          500: 'rgb(var(--ts-slate-500) / <alpha-value>)',
          600: 'rgb(var(--ts-slate-600) / <alpha-value>)',
          700: 'rgb(var(--ts-slate-700) / <alpha-value>)',
          800: 'rgb(var(--ts-slate-800) / <alpha-value>)',
          900: 'rgb(var(--ts-slate-900) / <alpha-value>)',
          950: 'rgb(var(--ts-slate-950) / <alpha-value>)',
        },
        /* Cyan text shades used inside panels — remapped per theme so
           `text-cyan-100` stays readable on white cards in light mode. */
        cyan: {
          100: 'rgb(var(--ts-cyan-100) / <alpha-value>)',
        },
        emerald: {
          300: 'rgb(var(--ts-emerald-300) / <alpha-value>)',
          400: 'rgb(var(--ts-emerald-400) / <alpha-value>)',
        },
      },
    },
  },
  plugins: [],
}
